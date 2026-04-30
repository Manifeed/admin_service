from sqlalchemy.orm import Session

from ..database.rss_feed_database_client import (
    list_rss_company_reads as list_rss_company_reads_from_storage,
    list_rss_feed_reads as list_rss_feed_reads_from_storage,
)
from shared_backend.schemas.rss.rss_company_schema import RssCompanyRead
from shared_backend.schemas.rss.rss_feed_schema import RssFeedRead


def list_rss_company_reads(db: Session) -> list[RssCompanyRead]:
    return list_rss_company_reads_from_storage(db)


def list_rss_feed_reads(db: Session, *, company_id: int | None = None) -> list[RssFeedRead]:
    return list_rss_feed_reads_from_storage(db, company_id=company_id)
