from sqlalchemy.orm import Session

from ..database.rss_toggle_database_client import (
    get_rss_company_toggle_state,
    get_rss_feed_toggle_state,
    update_rss_company_enabled,
    update_rss_feed_enabled,
)
from app.errors.custom_exceptions import (
    RssCompanyNotFoundError,
    RssFeedNotFoundError,
    RssFeedToggleForbiddenError,
)
from app.schemas.rss.rss_enabled_toggle_schema import (
    RssCompanyEnabledToggleRead,
    RssFeedEnabledToggleRead,
)

from .rss_job_lock_service import run_locked_rss_action


def toggle_rss_feed_enabled(
    db: Session,
    feed_id: int,
    enabled: bool,
) -> RssFeedEnabledToggleRead:
    return run_locked_rss_action(
        db,
        lock_name="rss_patch_feed_enabled",
        lock_error_message="RSS feed toggle already running",
        action=lambda: _toggle_rss_feed_enabled(db, feed_id=feed_id, enabled=enabled),
    )


def _toggle_rss_feed_enabled(
    db: Session,
    *,
    feed_id: int,
    enabled: bool,
) -> RssFeedEnabledToggleRead:
    feed_state = get_rss_feed_toggle_state(db, feed_id)
    if feed_state is None:
        raise RssFeedNotFoundError(f"RSS feed {feed_id} not found")
    if feed_state["company_id"] is not None and feed_state["company_enabled"] is False:
        raise RssFeedToggleForbiddenError(
            f"Cannot toggle feed {feed_id}: company '{feed_state['company_name']}' is disabled"
        )
    if feed_state["enabled"] == enabled:
        return RssFeedEnabledToggleRead(feed_id=feed_id, enabled=enabled)

    _commit_toggle_result(
        db,
        updated=update_rss_feed_enabled(db, feed_id, enabled),
        not_found_error=RssFeedNotFoundError(f"RSS feed {feed_id} not found"),
    )

    return RssFeedEnabledToggleRead(feed_id=feed_id, enabled=enabled)


def toggle_rss_company_enabled(
    db: Session,
    company_id: int,
    enabled: bool,
) -> RssCompanyEnabledToggleRead:
    return run_locked_rss_action(
        db,
        lock_name="rss_patch_company_enabled",
        lock_error_message="RSS company toggle already running",
        action=lambda: _toggle_rss_company_enabled(
            db,
            company_id=company_id,
            enabled=enabled,
        ),
    )


def _toggle_rss_company_enabled(
    db: Session,
    *,
    company_id: int,
    enabled: bool,
) -> RssCompanyEnabledToggleRead:
    company_state = get_rss_company_toggle_state(db, company_id)
    if company_state is None:
        raise RssCompanyNotFoundError(f"RSS company {company_id} not found")
    if company_state["enabled"] == enabled:
        return RssCompanyEnabledToggleRead(company_id=company_id, enabled=enabled)

    _commit_toggle_result(
        db,
        updated=update_rss_company_enabled(db, company_id, enabled),
        not_found_error=RssCompanyNotFoundError(f"RSS company {company_id} not found"),
    )

    return RssCompanyEnabledToggleRead(company_id=company_id, enabled=enabled)


def _commit_toggle_result(
    db: Session,
    *,
    updated: bool,
    not_found_error: Exception,
) -> None:
    try:
        if not updated:
            raise not_found_error
        db.commit()
    except Exception:
        db.rollback()
        raise
