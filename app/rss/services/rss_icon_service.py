from pathlib import Path

from ..networking.resolve_rss_icon_path import resolve_rss_icon_file_path
from app.rss.domain.rss_repository_config import get_rss_feeds_repository_path


def get_rss_icon_file_path(icon_url: str) -> Path:
    return resolve_rss_icon_file_path(
        repository_path=get_rss_feeds_repository_path(),
        icon_url=icon_url,
    )
