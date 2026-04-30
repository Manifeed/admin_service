from fastapi import APIRouter, Depends, Path, Query

from shared_backend.security.internal_service_auth import require_internal_service_token
from shared_backend.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from shared_backend.schemas.auth.auth_schema import UserRole
from app.services import admin_users_service


admin_users_router = APIRouter(
    prefix="/internal/admin/users",
    tags=["internal-admin-users"],
    dependencies=[Depends(require_internal_service_token)],
)


@admin_users_router.get("", response_model=AdminUserListRead)
def read_admin_users_route(
    role: UserRole | None = Query(default=None),
    is_active: bool | None = Query(default=None),
    api_access_enabled: bool | None = Query(default=None),
    search: str | None = Query(default=None, min_length=1, max_length=320),
    limit: int = Query(default=100, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> AdminUserListRead:
    return admin_users_service.read_admin_users(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
        limit=limit,
        offset=offset,
    )


@admin_users_router.patch("/{user_id}", response_model=AdminUserRead)
def update_admin_user_route(
    payload: AdminUserUpdateRequestSchema,
    user_id: int = Path(ge=1),
) -> AdminUserRead:
    return admin_users_service.update_admin_user(user_id=user_id, payload=payload)
