from sqlalchemy import text
from sqlalchemy.orm import Session

from app.schemas.rss.rss_company_schema import RssCompanyRead
from app.schemas.rss.rss_feed_schema import RssFeedRead
from app.utils.public_url_utils import normalize_public_http_url


def list_rss_company_reads(db: Session) -> list[RssCompanyRead]:
    rows = (
        db.execute(
            text(
                """
                SELECT DISTINCT
                    company.id,
                    company.name,
                    company.icon_url,
                    company.enabled
                FROM rss_company AS company
                JOIN rss_feeds AS feed
                    ON feed.company_id = company.id
                ORDER BY company.name ASC, company.id ASC
                """
            )
        )
        .mappings()
        .all()
    )
    return [_to_rss_company_read(row) for row in rows]


def list_rss_feed_reads(db: Session, *, company_id: int | None = None) -> list[RssFeedRead]:
    query = """
        SELECT
            feed.id,
            feed.url,
            feed.section,
            feed.enabled,
            feed.trust_score,
            company.id AS company_id,
            company.name AS company_name,
            company.icon_url AS company_icon_url,
            company.enabled AS company_enabled,
            COALESCE(company.fetchprotection, 1) AS fetchprotection,
            COALESCE(runtime.consecutive_error_count, 0) AS consecutive_error_count,
            runtime.last_error_code
        FROM rss_feeds AS feed
        LEFT JOIN rss_company AS company
            ON company.id = feed.company_id
        LEFT JOIN rss_feed_runtime AS runtime
            ON runtime.feed_id = feed.id
    """
    params: dict[str, int] = {}
    if company_id is not None:
        query += "\nWHERE feed.company_id = :company_id"
        params["company_id"] = company_id

    query += "\nORDER BY feed.id ASC"

    rows = db.execute(text(query), params).mappings().all()
    return [_to_rss_feed_read(row) for row in rows]


def _to_rss_company_read(row: object) -> RssCompanyRead:
    mapping = dict(row)
    return RssCompanyRead(
        id=int(mapping["id"]),
        name=str(mapping["name"]),
        icon_url=str(mapping["icon_url"]) if mapping["icon_url"] is not None else None,
        enabled=bool(mapping["enabled"]),
    )


def _to_rss_feed_read(row: object) -> RssFeedRead:
    mapping = dict(row)
    company_id = mapping.get("company_id")

    return RssFeedRead(
        id=                 int(mapping["id"]),
        url=                normalize_public_http_url(str(mapping["url"])),
        section=            str(mapping["section"]) if mapping["section"] is not None else None,
        enabled=            bool(mapping["enabled"]),
        trust_score=        float(mapping["trust_score"]),
        fetchprotection=    int(mapping["fetchprotection"]),
        consecutive_error_count=int(mapping["consecutive_error_count"]),
        last_error_code=(
            int(mapping["last_error_code"]) if mapping["last_error_code"] is not None else None
        ),
        company=(
            RssCompanyRead(
                id=                 int(company_id),
                name=               str(mapping["company_name"]),
                icon_url=           str(mapping["company_icon_url"]) if mapping["company_icon_url"] is not None else None,
                enabled=            bool(mapping["company_enabled"]),
            )
            if company_id is not None
            else None
        ),
    )
