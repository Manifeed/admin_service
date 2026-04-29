from typing import TypedDict
from sqlalchemy import text
from sqlalchemy.orm import Session


class RssFeedToggleState(TypedDict):
    feed_id: int
    enabled: bool
    company_id: int | None
    company_name: str | None
    company_enabled: bool | None


class RssCompanyToggleState(TypedDict):
    company_id: int
    enabled: bool


def get_rss_feed_toggle_state(db: Session, feed_id: int) -> RssFeedToggleState | None:
    row = (
        db.execute(
            text(
                """
                SELECT
                    feed.id AS feed_id,
                    feed.enabled AS enabled,
                    company.id AS company_id,
                    company.name AS company_name,
                    company.enabled AS company_enabled
                FROM rss_feeds AS feed
                LEFT JOIN rss_company AS company
                    ON company.id = feed.company_id
                WHERE feed.id = :feed_id
                """
            ),
            {"feed_id": feed_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        return None

    return RssFeedToggleState(
        feed_id=int(row["feed_id"]),
        enabled=bool(row["enabled"]),
        company_id=(int(row["company_id"]) if row["company_id"] is not None else None),
        company_name=(str(row["company_name"]) if row["company_name"] is not None else None),
        company_enabled=(
            bool(row["company_enabled"]) if row["company_enabled"] is not None else None
        ),
    )


def get_rss_company_toggle_state(db: Session, company_id: int) -> RssCompanyToggleState | None:
    row = (
        db.execute(
            text(
                """
                SELECT
                    company.id AS company_id,
                    company.enabled AS enabled
                FROM rss_company AS company
                WHERE company.id = :company_id
                """
            ),
            {"company_id": company_id},
        )
        .mappings()
        .first()
    )
    if row is None:
        return None

    return RssCompanyToggleState(
        company_id=int(row["company_id"]),
        enabled=bool(row["enabled"]),
    )


def update_rss_feed_enabled(db: Session, feed_id: int, enabled: bool) -> bool:
    result = db.execute(
        text(
            """
            UPDATE rss_feeds
            SET enabled = :enabled
            WHERE id = :feed_id
            """
        ),
        {"feed_id": feed_id, "enabled": enabled},
    )
    return result.rowcount > 0


def update_rss_company_enabled(db: Session, company_id: int, enabled: bool) -> bool:
    result = db.execute(
        text(
            """
            UPDATE rss_company
            SET enabled = :enabled
            WHERE id = :company_id
            """
        ),
        {"company_id": company_id, "enabled": enabled},
    )
    return result.rowcount > 0
