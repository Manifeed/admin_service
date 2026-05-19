from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path
from sqlalchemy.orm import Session

from app.database import get_identity_read_db_session, get_identity_write_db_session
from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.security.internal_service_auth import require_internal_service_token
from shared_backend.schemas.admin.admin_user_schema import AdminUserListRead, AdminUserRead
from shared_backend.schemas.internal.user_service_schema import (
    InternalCurrentUserPayload,
    InternalAdminUserListRequest,
    InternalAdminUserUpdateRequest,
)
from app.services import admin_users_service


admin_users_router = APIRouter(
    prefix="/internal/admin/users",
    tags=["internal-admin-users"],
    dependencies=[Depends(require_internal_service_token)],
)


@admin_users_router.post("/list", response_model=AdminUserListRead)
def read_admin_users_route(
    payload: Annotated[InternalAdminUserListRequest, Body(embed=True)],
    db: Session = Depends(get_identity_read_db_session),
) -> AdminUserListRead:
    return admin_users_service.read_admin_users(
        db=db,
        current_user=_to_current_user_context(payload.current_user),
        role=payload.filters.role,
        is_active=payload.filters.is_active,
        api_access_enabled=payload.filters.api_access_enabled,
        search=payload.filters.search,
        limit=payload.filters.limit,
        offset=payload.filters.offset,
    )


@admin_users_router.patch("/{user_id}", response_model=AdminUserRead)
def update_admin_user_route(
    payload: Annotated[InternalAdminUserUpdateRequest, Body(embed=True)],
    user_id: int = Path(ge=1),
    db: Session = Depends(get_identity_write_db_session),
) -> AdminUserRead:
    return admin_users_service.update_admin_user(
        db=db,
        current_user=_to_current_user_context(payload.current_user),
        user_id=user_id,
        payload=payload.payload,
    )


def _to_current_user_context(payload: InternalCurrentUserPayload) -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=payload.user_id,
        email=payload.email,
        role=payload.role,
        is_active=payload.is_active,
        api_access_enabled=payload.api_access_enabled,
        session_expires_at=payload.session_expires_at,
    )
