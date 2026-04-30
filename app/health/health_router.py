from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from shared_backend.security.internal_service_auth import require_internal_service_token
from shared_backend.schemas.health import HealthRead

from .health_service import get_health_status
from database import get_content_db_session, get_identity_db_session

health_router = APIRouter(
    prefix="/internal/admin/health",
    tags=["health"],
    dependencies=[Depends(require_internal_service_token)],
)


@health_router.get("/", response_model=HealthRead)
def read_health(
    content_db: Session = Depends(get_content_db_session),
    identity_db: Session = Depends(get_identity_db_session),
) -> HealthRead:
    return get_health_status(content_db, identity_db)
