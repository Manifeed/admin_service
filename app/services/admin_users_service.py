from __future__ import annotations

from app.clients.networking.user_service_networking_client import get_required_user_service_client
from app.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from app.schemas.auth.auth_schema import UserRole


def read_admin_users(
    *,
    role: UserRole | None,
    is_active: bool | None,
    api_access_enabled: bool | None,
    search: str | None,
    limit: int,
    offset: int,
) -> AdminUserListRead:
    return get_required_user_service_client().read_admin_users(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
        limit=limit,
        offset=offset,
    )


def update_admin_user(
    *,
    user_id: int,
    payload: AdminUserUpdateRequestSchema,
) -> AdminUserRead:
    return get_required_user_service_client().update_admin_user(
        user_id=user_id,
        payload=payload,
    )
