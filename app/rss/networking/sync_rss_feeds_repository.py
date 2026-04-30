import json
from pathlib import Path
from pydantic import ValidationError

from shared_backend.errors.custom_exceptions import RssCatalogParseError
from shared_backend.schemas.rss.rss_source_feed_schema import RssSourceCatalogSchema
from shared_backend.schemas.rss.rss_sync_schema import RssRepositorySyncRead

from app.utils.directory_utils import list_files_on_dir_with_ext
from app.utils.git_repository_utils import list_changed_files, pull_or_clone


_CATALOG_DIR = "json"

def sync_rss_feeds_repository(
    repository_url: str,
    repository_path: Path | str,
    branch: str,
) -> RssRepositorySyncRead:
    repository_path = Path(repository_path).expanduser()

    repository_sync = pull_or_clone(
        repository_url=repository_url,
        repository_path=repository_path,
        branch=branch,
    )
    changed_files = _list_changed_catalog_files(
        repository_path=repository_path,
        previous_revision=repository_sync.previous_revision,
        current_revision=repository_sync.current_revision,
    )

    return RssRepositorySyncRead(
        action=repository_sync.action,
        repository_path=str(repository_path),
        previous_revision=repository_sync.previous_revision,
        current_revision=repository_sync.current_revision,
        changed_files=changed_files,
    )


def load_source_feeds_from_json(json_file_path: Path) -> RssSourceCatalogSchema:
    if not json_file_path.is_file():
        raise RssCatalogParseError(f"JSON file not found: {json_file_path}")

    try:
        with json_file_path.open(encoding="utf-8") as json_file:
            payload = json.load(json_file)
    except json.JSONDecodeError as exception:
        raise RssCatalogParseError(
            f"Invalid JSON format in file {json_file_path}: {exception}"
        ) from exception

    if not isinstance(payload, dict):
        raise RssCatalogParseError(
            f"Expected an object payload in file {json_file_path}, got {type(payload).__name__}"
        )

    try:
        return RssSourceCatalogSchema.model_validate(payload)
    except ValidationError as exception:
        raise RssCatalogParseError(
            f"Invalid catalog payload in file {json_file_path}: {exception}"
        ) from exception


def _list_changed_catalog_files(
    *,
    repository_path: Path,
    previous_revision: str | None,
    current_revision: str | None,
) -> list[str]:
    if not current_revision:
        return []

    if not previous_revision:
        catalog_repository_path = repository_path / _CATALOG_DIR
        if not catalog_repository_path.exists():
            return []

        return [
            f"{_CATALOG_DIR}/{relative_path}"
            for relative_path in sorted(
                list_files_on_dir_with_ext(
                    repository_path=catalog_repository_path,
                    file_extension=".json",
                )
            )
        ]

    if previous_revision == current_revision:
        return []

    return [
        changed_file
        for changed_file in list_changed_files(
            repository_path=repository_path,
            old_revision=previous_revision,
            new_revision=current_revision,
            file_extension=".json",
        )
        if changed_file.startswith(f"{_CATALOG_DIR}/")
    ]
