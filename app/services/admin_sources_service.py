from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database.source_read_detail_database_client import get_rss_source_detail_read_by_id
from app.clients.database.source_read_listing_database_client import list_rss_sources_read

from shared_backend.errors.custom_exceptions import SourceNotFoundError
from shared_backend.schemas.sources.source_schema import RssSourceDetailRead, RssSourcePageRead


def list_admin_sources(
    db: Session,
    *,
    limit: int,
    offset: int,
    feed_id: int | None = None,
    company_id: int | None = None,
    author_id: int | None = None,
) -> RssSourcePageRead:
    items, total = list_rss_sources_read(
        db,
        limit=limit,
        offset=offset,
        feed_id=feed_id,
        company_id=company_id,
        author_id=author_id,
    )
    return RssSourcePageRead(
        items=items,
        total=total,
        limit=limit,
        offset=offset,
    )


def read_admin_source(
    db: Session,
    *,
    source_id: int,
) -> RssSourceDetailRead:
    payload = get_rss_source_detail_read_by_id(db, source_id)
    if payload is None:
        raise SourceNotFoundError(f"RSS source {source_id} not found")
    return payload
