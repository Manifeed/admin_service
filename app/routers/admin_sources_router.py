from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import get_content_read_db_session
from app.services import admin_sources_service

from shared_backend.security.internal_service_auth import require_internal_service_token
from shared_backend.schemas.sources.source_schema import RssSourceDetailRead, RssSourcePageRead


admin_sources_router = APIRouter(
    prefix="/internal/admin/sources",
    tags=["internal-admin-sources"],
    dependencies=[Depends(require_internal_service_token)],
)


@admin_sources_router.get("/", response_model=RssSourcePageRead)
def read_admin_sources(
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_content_read_db_session),
) -> RssSourcePageRead:
    return admin_sources_service.list_admin_sources(
        db,
        limit=limit,
        offset=offset,
        author_id=author_id,
    )


@admin_sources_router.get("/feeds/{feed_id}", response_model=RssSourcePageRead)
def read_admin_sources_by_feed(
    feed_id: int = Path(ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_content_read_db_session),
) -> RssSourcePageRead:
    return admin_sources_service.list_admin_sources(
        db,
        limit=limit,
        offset=offset,
        feed_id=feed_id,
        author_id=author_id,
    )


@admin_sources_router.get("/companies/{company_id}", response_model=RssSourcePageRead)
def read_admin_sources_by_company(
    company_id: int = Path(ge=1),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    author_id: int | None = Query(default=None, ge=1),
    db: Session = Depends(get_content_read_db_session),
) -> RssSourcePageRead:
    return admin_sources_service.list_admin_sources(
        db,
        limit=limit,
        offset=offset,
        company_id=company_id,
        author_id=author_id,
    )


@admin_sources_router.get("/{source_id}", response_model=RssSourceDetailRead)
def read_admin_source_by_id(
    source_id: int = Path(ge=1),
    db: Session = Depends(get_content_read_db_session),
) -> RssSourceDetailRead:
    return admin_sources_service.read_admin_source(db, source_id=source_id)
