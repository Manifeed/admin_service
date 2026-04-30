from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
import logging
from pathlib import Path
from sqlalchemy.orm import Session

from ..database.rss_catalog_database_client import (
    bulk_replace_rss_feed_tags,
    bulk_upsert_rss_catalog_feeds,
    delete_rss_companies_without_feeds,
    delete_rss_company_feeds_not_in_urls,
    list_rss_companies_with_feeds,
    upsert_rss_catalog_company,
)
from ..database.rss_catalog_sync_database_client import (
    get_rss_catalog_sync_state,
    mark_rss_catalog_sync_failure,
    mark_rss_catalog_sync_success,
)
from ..networking.sync_rss_feeds_repository import (
    load_source_feeds_from_json,
    sync_rss_feeds_repository,
)
from ..domain.rss_catalog_normalization import (
    normalize_country,
    normalize_name_from_filename,
)
from ..domain.rss_repository_config import (
    get_rss_feeds_repository_branch,
    get_rss_feeds_repository_path,
    get_rss_feeds_repository_url,
)
from ..domain.rss_sync_normalization import normalize_source_feed_entry
from .rss_job_lock_service import run_locked_rss_action

from shared_backend.errors.custom_exceptions import RssRepositorySyncError
from shared_backend.schemas.rss.rss_sync_schema import RssRepositorySyncRead, RssSyncRead
from app.utils.directory_utils import list_files_on_dir_with_ext
from app.utils.git_repository_utils import GitRepositorySyncError, list_changed_files


logger = logging.getLogger(__name__)
_CATALOG_DIR = "json"


@dataclass(slots=True)
class _CatalogReconcileResult:
    files_processed: int = 0
    companies_removed: int = 0
    feeds_removed: int = 0


@dataclass(slots=True)
class _CatalogSyncPlan:
    relative_catalog_paths: list[str]
    should_apply_catalog_changes: bool


def sync_rss_catalog(db: Session, force: bool = False) -> RssSyncRead:
    return run_locked_rss_action(
        db,
        lock_name="rss_sync",
        lock_error_message="RSS sync already running",
        action=lambda: _sync_rss_catalog(db, force=force),
    )


def _sync_rss_catalog(db: Session, force: bool = False) -> RssSyncRead:
    repository_path = get_rss_feeds_repository_path()
    try:
        repository_sync = sync_rss_feeds_repository(
            repository_url=get_rss_feeds_repository_url(),
            repository_path=repository_path,
            branch=get_rss_feeds_repository_branch(),
        )
    except GitRepositorySyncError as exception:
        raise RssRepositorySyncError("RSS repository sync failed") from exception
    _log_repository_sync_action(repository_sync)

    sync_state = get_rss_catalog_sync_state(db)
    last_applied_revision = sync_state.last_applied_revision if sync_state is not None else None
    should_reconcile = force or repository_sync.current_revision != last_applied_revision

    if not should_reconcile:
        return _build_sync_response(
            repository_sync,
            mode="noop",
            applied_from_revision=last_applied_revision,
            reconcile_result=_CatalogReconcileResult(),
        )

    sync_plan = _build_catalog_sync_plan(
        repository_path=repository_path,
        repository_sync=repository_sync,
        last_applied_revision=last_applied_revision,
        force=force,
    )

    try:
        reconcile_result = (
            _reconcile_rss_catalog(
                db,
                repository_path=repository_path,
                relative_catalog_paths=sync_plan.relative_catalog_paths,
            )
            if sync_plan.should_apply_catalog_changes
            else _CatalogReconcileResult()
        )
        mark_rss_catalog_sync_success(
            db,
            current_revision=repository_sync.current_revision,
        )
        db.commit()
    except Exception as exception:
        db.rollback()
        _persist_catalog_sync_failure(
            db,
            current_revision=repository_sync.current_revision,
            error_message=str(exception),
        )
        raise

    return _build_sync_response(
        repository_sync,
        mode=("full_reconcile" if sync_plan.should_apply_catalog_changes else "noop"),
        applied_from_revision=last_applied_revision,
        reconcile_result=reconcile_result,
    )


def _reconcile_rss_catalog(
    db: Session,
    *,
    repository_path: Path,
    relative_catalog_paths: Sequence[str] | None = None,
) -> _CatalogReconcileResult:
    result = _CatalogReconcileResult()
    catalog_repository_path = repository_path / _CATALOG_DIR
    catalog_paths_to_sync = (
        sorted(set(relative_catalog_paths))
        if relative_catalog_paths is not None
        else _list_catalog_relative_paths(catalog_repository_path)
    )

    for relative_catalog_path in catalog_paths_to_sync:
        _company_id, feeds_removed = _sync_catalog_file(
            db,
            catalog_repository_path=catalog_repository_path,
            relative_json_file_path=relative_catalog_path,
        )
        result.files_processed += 1
        result.feeds_removed += feeds_removed

    _flush_pending_catalog_changes(db)
    result.feeds_removed += _prune_companies_not_in_catalog(
        db,
        catalog_repository_path=catalog_repository_path,
    )
    _flush_pending_catalog_changes(db)
    result.companies_removed = delete_rss_companies_without_feeds(db)
    return result


def _sync_catalog_file(
    db: Session,
    *,
    catalog_repository_path: Path,
    relative_json_file_path: str,
) -> tuple[int, int]:
    catalog_file_path = catalog_repository_path / relative_json_file_path
    catalog = load_source_feeds_from_json(catalog_file_path)
    company_fetchprotection = max(0, min(2, catalog.fetchprotection))
    company_id = upsert_rss_catalog_company(
        db,
        company_name=catalog.company.strip(),
        host=catalog.host,
        icon_url=(catalog.img.strip() if catalog.img else None),
        country=normalize_country(catalog.country),
        language=normalize_country(catalog.language),
        fetchprotection=company_fetchprotection,
    )
    expected_urls: set[str] = set()
    feed_payloads_by_url = {}
    for source_feed in catalog.feeds:
        payload = normalize_source_feed_entry(
            source_feed,
            default_fetchprotection=company_fetchprotection,
        )
        expected_urls.add(payload.url)
        feed_payloads_by_url[payload.url] = payload

    feed_payloads = list(feed_payloads_by_url.values())
    feed_ids_by_url = bulk_upsert_rss_catalog_feeds(
        db,
        company_id=company_id,
        payloads=feed_payloads,
    )
    bulk_replace_rss_feed_tags(
        db,
        tag_names_by_feed_id={
            feed_ids_by_url[payload.url]: payload.tags
            for payload in feed_payloads
            if payload.url in feed_ids_by_url
        },
    )

    _flush_pending_catalog_changes(db)
    feeds_removed = delete_rss_company_feeds_not_in_urls(
        db,
        company_id=company_id,
        expected_urls=expected_urls,
    )
    return company_id, feeds_removed


def _flush_pending_catalog_changes(db: Session) -> None:
    # The backend session runs with autoflush disabled, so cleanup queries must
    # explicitly flush pending feed/company links before they inspect the DB.
    db.flush()


def _persist_catalog_sync_failure(
    db: Session,
    *,
    current_revision: str | None,
    error_message: str,
) -> None:
    try:
        mark_rss_catalog_sync_failure(
            db,
            current_revision=current_revision,
            error_message=error_message,
        )
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("rss_sync - unable to persist sync failure state")


def _build_sync_response(
    repository_sync: RssRepositorySyncRead,
    *,
    mode: str,
    applied_from_revision: str | None,
    reconcile_result: _CatalogReconcileResult,
) -> RssSyncRead:
    return RssSyncRead(
        repository_action=repository_sync.action,
        mode=mode,
        current_revision=repository_sync.current_revision,
        applied_from_revision=applied_from_revision,
        files_processed=reconcile_result.files_processed,
        companies_removed=reconcile_result.companies_removed,
        feeds_removed=reconcile_result.feeds_removed,
    )


def _log_repository_sync_action(repository_sync: RssRepositorySyncRead) -> None:
    if repository_sync.action == "up_to_date":
        logger.info("rss_sync - repository up to date")
        return

    if repository_sync.action == "cloned":
        logger.info("rss_sync - repository cloned")
        return

    logger.info("rss_sync - repository updated")


def _build_catalog_sync_plan(
    *,
    repository_path: Path,
    repository_sync: RssRepositorySyncRead,
    last_applied_revision: str | None,
    force: bool,
) -> _CatalogSyncPlan:
    catalog_repository_path = repository_path / _CATALOG_DIR
    if force or last_applied_revision is None:
        return _CatalogSyncPlan(
            relative_catalog_paths=_list_catalog_relative_paths(catalog_repository_path),
            should_apply_catalog_changes=True,
        )

    changed_catalog_files = _list_changed_catalog_files_since_last_apply(
        repository_path=repository_path,
        repository_sync=repository_sync,
        last_applied_revision=last_applied_revision,
    )
    relative_catalog_paths = _filter_existing_catalog_paths(
        catalog_repository_path=catalog_repository_path,
        changed_catalog_files=changed_catalog_files,
    )
    return _CatalogSyncPlan(
        relative_catalog_paths=relative_catalog_paths,
        should_apply_catalog_changes=bool(changed_catalog_files),
    )


def _list_changed_catalog_files_since_last_apply(
    *,
    repository_path: Path,
    repository_sync: RssRepositorySyncRead,
    last_applied_revision: str,
) -> list[str]:
    if repository_sync.current_revision is None or repository_sync.current_revision == last_applied_revision:
        return []

    if repository_sync.previous_revision == last_applied_revision:
        return [
            changed_file
            for changed_file in repository_sync.changed_files
            if changed_file.startswith(f"{_CATALOG_DIR}/")
        ]

    return [
        changed_file
        for changed_file in list_changed_files(
            repository_path=repository_path,
            old_revision=last_applied_revision,
            new_revision=repository_sync.current_revision,
            file_extension=".json",
        )
        if changed_file.startswith(f"{_CATALOG_DIR}/")
    ]


def _filter_existing_catalog_paths(
    *,
    catalog_repository_path: Path,
    changed_catalog_files: Sequence[str],
) -> list[str]:
    return sorted(
        {
            relative_catalog_path
            for relative_catalog_path in (
                _to_catalog_relative_path(changed_file)
                for changed_file in changed_catalog_files
            )
            if relative_catalog_path is not None
            and (catalog_repository_path / relative_catalog_path).is_file()
        }
    )


def _prune_companies_not_in_catalog(
    db: Session,
    *,
    catalog_repository_path: Path,
) -> int:
    current_catalog_company_names = {
        normalize_name_from_filename(relative_catalog_path)
        for relative_catalog_path in _list_catalog_relative_paths(catalog_repository_path)
    }

    feeds_removed = 0
    for company_id, company_name in list_rss_companies_with_feeds(db):
        if company_name in current_catalog_company_names:
            continue
        feeds_removed += delete_rss_company_feeds_not_in_urls(
            db,
            company_id=company_id,
            expected_urls=set(),
        )
    return feeds_removed


def _list_catalog_relative_paths(catalog_repository_path: Path) -> list[str]:
    if not catalog_repository_path.exists():
        return []

    return sorted(
        list_files_on_dir_with_ext(
            repository_path=catalog_repository_path,
            file_extension=".json",
        )
    )


def _to_catalog_relative_path(changed_file: str) -> str | None:
    prefix = f"{_CATALOG_DIR}/"
    if not changed_file.startswith(prefix):
        return None

    relative_catalog_path = changed_file[len(prefix):].strip()
    if not relative_catalog_path:
        return None
    return relative_catalog_path
