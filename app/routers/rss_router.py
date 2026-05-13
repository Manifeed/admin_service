from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from shared_backend.schemas.rss.rss_enabled_toggle_schema import (
    RssCompanyEnabledToggleRead,
    RssFeedEnabledToggleRead,
    RssEnabledTogglePayload,
)
from shared_backend.schemas.rss.rss_company_schema import RssCompanyRead
from shared_backend.schemas.rss.rss_feed_schema import RssFeedRead
from shared_backend.schemas.rss.rss_sync_schema import RssSyncRead

from shared_backend.security.internal_service_auth import require_internal_service_token
from app.services.rss_feed_service import list_rss_company_reads, list_rss_feed_reads
from app.services.rss_sync_service import sync_rss_catalog
from app.services.rss_toggle_service import toggle_rss_company_enabled, toggle_rss_feed_enabled

from app.database import get_content_read_db_session, get_content_write_db_session

rss_admin_router = APIRouter(
    prefix="/internal/admin/rss",
    tags=["rss"],
    dependencies=[Depends(require_internal_service_token)],
)

@rss_admin_router.get("/companies", response_model=list[RssCompanyRead])
def read_rss_companies(
    db: Session = Depends(get_content_read_db_session),
) -> list[RssCompanyRead]:
    return list_rss_company_reads(db)


@rss_admin_router.get("/", response_model=list[RssFeedRead])
def read_rss_feeds(
    company_id: Annotated[int | None, Query(ge=1)] = None,
    db: Session = Depends(get_content_read_db_session),
) -> list[RssFeedRead]:
    return list_rss_feed_reads(db, company_id=company_id)


@rss_admin_router.patch("/feeds/{feed_id}/enabled", response_model=RssFeedEnabledToggleRead)
def update_rss_feed_enabled(
    feed_id: Annotated[int, Path(ge=1)],
    payload: Annotated[RssEnabledTogglePayload, Body(embed=True)],
    db: Session = Depends(get_content_write_db_session),
) -> RssFeedEnabledToggleRead:
    return toggle_rss_feed_enabled(
        db,
        feed_id=feed_id,
        enabled=payload.enabled,
    )


@rss_admin_router.patch("/companies/{company_id}/enabled", response_model=RssCompanyEnabledToggleRead)
def update_rss_company_enabled(
    company_id: Annotated[int, Path(ge=1)],
    payload: Annotated[RssEnabledTogglePayload, Body(embed=True)],
    db: Session = Depends(get_content_write_db_session),
) -> RssCompanyEnabledToggleRead:
    return toggle_rss_company_enabled(
        db,
        company_id=company_id,
        enabled=payload.enabled,
    )


@rss_admin_router.post("/sync", response_model=RssSyncRead)
def sync_rss_feeds(
    force: bool = Query(default=False, description="Force full catalog reprocessing"),
    db: Session = Depends(get_content_write_db_session),
) -> RssSyncRead:
    return sync_rss_catalog(db, force=force)
