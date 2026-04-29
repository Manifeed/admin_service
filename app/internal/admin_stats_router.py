from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.admin.services.admin_stats_service import read_admin_stats
from app.clients.networking.worker_service_networking_client import get_required_worker_service_client
from app.internal.security import require_internal_service_token
from app.schemas.admin.admin_stats_schema import AdminStatsRead
from database import get_content_db_session, get_identity_db_session

internal_admin_stats_router = APIRouter(
    prefix="/internal/admin",
    tags=["internal-admin"],
    dependencies=[Depends(require_internal_service_token)],
)


@internal_admin_stats_router.get("/stats", response_model=AdminStatsRead)
def read_internal_admin_stats(
    identity_db: Session = Depends(get_identity_db_session),
    content_db: Session = Depends(get_content_db_session),
) -> AdminStatsRead:
    stats = read_admin_stats(identity_db, content_db)
    worker_stats = get_required_worker_service_client().read_worker_stats()
    return stats.model_copy(update={"connected_workers": worker_stats.connected_workers})
