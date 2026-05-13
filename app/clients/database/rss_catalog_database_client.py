from __future__ import annotations

from collections.abc import Mapping, Sequence
import sqlalchemy as sa
from sqlalchemy import select, text
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models.rss_company_model import RssCompany
from app.models.rss_feed_model import RssFeed
from app.models.rss_feed_tag_model import RssFeedTag
from app.models.rss_tag_model import RssTag
from shared_backend.schemas.rss.rss_feed_upsert_schema import RssFeedUpsertSchema

_BATCH_SIZE = 1000

def upsert_rss_catalog_company(
    db: Session,
    *,
    company_name: str,
    host: str | None,
    icon_url: str | None,
    country: str | None,
    fetchprotection: int,
) -> int:
    row = (
        db.execute(
            text(
                """
                INSERT INTO rss_company (
                    name,
                    host,
                    icon_url,
                    country,
                    fetchprotection,
                    enabled
                ) VALUES (
                    :company_name,
                    :host,
                    :icon_url,
                    :country,
                    :fetchprotection,
                    TRUE
                )
                ON CONFLICT (name) DO UPDATE
                SET
                    host = EXCLUDED.host,
                    icon_url = EXCLUDED.icon_url,
                    country = EXCLUDED.country,
                    fetchprotection = EXCLUDED.fetchprotection
                RETURNING id
                """
            ),
            {
                "company_name": company_name,
                "host": host,
                "icon_url": icon_url,
                "country": country or "xx",
                "fetchprotection": max(0, min(2, fetchprotection)),
            },
        )
        .mappings()
        .one()
    )
    return int(row["id"])


def bulk_upsert_rss_catalog_feeds(
    db: Session,
    *,
    company_id: int,
    payloads: Sequence[RssFeedUpsertSchema],
) -> dict[str, int]:
    normalized_payloads = list(_dedupe_feed_payloads(payloads))
    if not normalized_payloads:
        return {}

    feed_ids_by_url: dict[str, int] = {}
    for payload_batch in _iter_batches(normalized_payloads, batch_size=_BATCH_SIZE):
        statement = (
            insert(RssFeed)
            .values(
                [
                    {
                        "company_id": company_id,
                        "url": payload.url,
                        "section": payload.section,
                        "trust_score": payload.trust_score,
                        "enabled": payload.enabled,
                    }
                    for payload in payload_batch
                ]
            )
            .on_conflict_do_update(
                index_elements=[RssFeed.url],
                set_={
                    "company_id": sa.text("EXCLUDED.company_id"),
                    "section": sa.text("EXCLUDED.section"),
                    "trust_score": sa.text("EXCLUDED.trust_score"),
                    "enabled": sa.text("EXCLUDED.enabled"),
                },
            )
            .returning(RssFeed.id, RssFeed.url)
        )
        rows = db.execute(statement).all()
        for feed_id, url in rows:
            feed_ids_by_url[str(url)] = int(feed_id)

    return feed_ids_by_url


def upsert_rss_catalog_feed(
    db: Session,
    *,
    company_id: int,
    payload: RssFeedUpsertSchema,
) -> int:
    row = (
        db.execute(
            text(
                """
                INSERT INTO rss_feeds (
                    company_id,
                    url,
                    section,
                    trust_score,
                    enabled
                ) VALUES (
                    :company_id,
                    :url,
                    :section,
                    :trust_score,
                    :enabled
                )
                ON CONFLICT (url) DO UPDATE
                SET
                    company_id = EXCLUDED.company_id,
                    section = EXCLUDED.section,
                    trust_score = EXCLUDED.trust_score,
                    enabled = EXCLUDED.enabled
                RETURNING id
                """
            ),
            {
                "company_id": company_id,
                "url": payload.url,
                "section": payload.section,
                "trust_score": payload.trust_score,
                "enabled": payload.enabled,
            },
        )
        .mappings()
        .one()
    )
    return int(row["id"])


def bulk_replace_rss_feed_tags(
    db: Session,
    *,
    tag_names_by_feed_id: Mapping[int, Sequence[str]],
) -> None:
    normalized_tags_by_feed_id = {
        feed_id: [tag_name for tag_name in dict.fromkeys(tag_names) if tag_name]
        for feed_id, tag_names in tag_names_by_feed_id.items()
    }
    if not normalized_tags_by_feed_id:
        return

    feed_ids = sorted(normalized_tags_by_feed_id)
    db.execute(sa.delete(RssFeedTag).where(RssFeedTag.feed_id.in_(feed_ids)))

    unique_tag_names = sorted(
        {
            tag_name
            for tag_names in normalized_tags_by_feed_id.values()
            for tag_name in tag_names
        }
    )
    if not unique_tag_names:
        return

    for tag_name_batch in _iter_batches(unique_tag_names, batch_size=_BATCH_SIZE):
        db.execute(
            insert(RssTag)
            .values([{"name": tag_name} for tag_name in tag_name_batch])
            .on_conflict_do_nothing(index_elements=[RssTag.name])
        )

    tag_ids_by_name = _list_rss_tag_ids_by_name(db, tag_names=unique_tag_names)
    feed_tag_links = [
        {
            "feed_id": feed_id,
            "tag_id": tag_ids_by_name[tag_name],
        }
        for feed_id, tag_names in normalized_tags_by_feed_id.items()
        for tag_name in tag_names
    ]
    if not feed_tag_links:
        return

    for feed_tag_batch in _iter_batches(feed_tag_links, batch_size=_BATCH_SIZE):
        db.execute(
            insert(RssFeedTag)
            .values(feed_tag_batch)
            .on_conflict_do_nothing(index_elements=[RssFeedTag.feed_id, RssFeedTag.tag_id])
        )


def replace_rss_feed_tags(
    db: Session,
    *,
    feed_id: int,
    tag_names: Sequence[str],
) -> None:
    normalized_tag_names = [tag_name for tag_name in dict.fromkeys(tag_names) if tag_name]

    db.execute(
        text(
            """
            DELETE FROM rss_feed_tags
            WHERE feed_id = :feed_id
            """
        ),
        {"feed_id": feed_id},
    )

    if not normalized_tag_names:
        return

    for tag_name in normalized_tag_names:
        tag_id = _get_or_create_rss_tag_id(db, tag_name)
        db.execute(
            text(
                """
                INSERT INTO rss_feed_tags (feed_id, tag_id)
                VALUES (:feed_id, :tag_id)
                ON CONFLICT (feed_id, tag_id) DO NOTHING
                """
            ),
            {
                "feed_id": feed_id,
                "tag_id": tag_id,
            },
        )


def delete_rss_company_feeds_not_in_urls(
    db: Session,
    *,
    company_id: int,
    expected_urls: Sequence[str],
) -> int:
    normalized_urls = sorted({url for url in expected_urls if url})
    if normalized_urls:
        result = db.execute(
            text(
                """
                DELETE FROM rss_feeds
                WHERE company_id = :company_id
                  AND NOT (url = ANY(:expected_urls))
                """
            ),
            {
                "company_id": company_id,
                "expected_urls": normalized_urls,
            },
        )
        return result.rowcount or 0

    result = db.execute(
        text(
            """
            DELETE FROM rss_feeds
            WHERE company_id = :company_id
            """
        ),
        {"company_id": company_id},
    )
    return result.rowcount or 0


def list_rss_company_ids_with_feeds(db: Session) -> list[int]:
    rows = (
        db.execute(
            text(
                """
                SELECT DISTINCT company_id
                FROM rss_feeds
                WHERE company_id IS NOT NULL
                ORDER BY company_id ASC
                """
            )
        )
        .mappings()
        .all()
    )
    return [int(row["company_id"]) for row in rows]


def list_rss_companies_with_feeds(db: Session) -> list[tuple[int, str]]:
    rows = (
        db.execute(
            select(RssCompany.id, RssCompany.name)
            .join(RssFeed, RssFeed.company_id == RssCompany.id)
            .distinct()
            .order_by(RssCompany.id.asc())
        )
        .all()
    )
    return [(int(company_id), str(company_name)) for company_id, company_name in rows]


def delete_rss_companies_without_feeds(db: Session) -> int:
    result = db.execute(
        text(
            """
            DELETE FROM rss_company AS company
            WHERE NOT EXISTS (
                SELECT 1
                FROM rss_feeds AS feed
                WHERE feed.company_id = company.id
            )
            """
        )
    )
    return result.rowcount or 0


def _get_or_create_rss_tag_id(db: Session, tag_name: str) -> int:
    db.execute(
        text(
            """
            INSERT INTO rss_tags (name)
            VALUES (:tag_name)
            ON CONFLICT (name) DO NOTHING
            """
        ),
        {"tag_name": tag_name},
    )
    row = (
        db.execute(
            text(
                """
                SELECT id
                FROM rss_tags
                WHERE name = :tag_name
                """
            ),
            {"tag_name": tag_name},
        )
        .mappings()
        .one()
    )
    return int(row["id"])


def _list_rss_tag_ids_by_name(
    db: Session,
    *,
    tag_names: Sequence[str],
) -> dict[str, int]:
    if not tag_names:
        return {}

    rows = db.execute(
        select(RssTag.id, RssTag.name).where(RssTag.name.in_(list(tag_names)))
    ).all()
    return {str(tag_name): int(tag_id) for tag_id, tag_name in rows}


def _dedupe_feed_payloads(
    payloads: Sequence[RssFeedUpsertSchema],
) -> list[RssFeedUpsertSchema]:
    payloads_by_url: dict[str, RssFeedUpsertSchema] = {}
    for payload in payloads:
        payloads_by_url[payload.url] = payload
    return list(payloads_by_url.values())


def _iter_batches(items: Sequence[object], *, batch_size: int) -> list[Sequence[object]]:
    return [items[index:index + batch_size] for index in range(0, len(items), batch_size)]
