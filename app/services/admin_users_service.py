from __future__ import annotations

from sqlalchemy.orm import Session

from app.clients.database import identity_user_database_client
from app.clients.database.identity_user_database_client import UserRecord
from app.services.current_user_context_service import ensure_admin_user

from shared_backend.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.errors.custom_exceptions import UserNotFoundError
from shared_backend.schemas.auth.auth_schema import UserRole


def read_admin_users(
    *,
    db: Session,
    current_user: AuthenticatedUserContext,
    role: UserRole | None,
    is_active: bool | None,
    api_access_enabled: bool | None,
    search: str | None,
    limit: int,
    offset: int,
) -> AdminUserListRead:
    ensure_admin_user(current_user)
    normalized_search = search.strip() if search is not None else None
    effective_search = normalized_search or None
    effective_is_active = is_active
    if effective_is_active is None and effective_search is None:
        effective_is_active = True

    items, total = identity_user_database_client.list_users(
        db,
        role=role,
        is_active=effective_is_active,
        api_access_enabled=api_access_enabled,
        search=effective_search,
        limit=limit,
        offset=offset,
    )
    return AdminUserListRead(
        items=[_build_admin_user_read(user) for user in items],
        total=total,
        active_total=identity_user_database_client.count_users(db, is_active=True),
        limit=limit,
        offset=offset,
    )


def update_admin_user(
    *,
    db: Session,
    current_user: AuthenticatedUserContext,
    user_id: int,
    payload: AdminUserUpdateRequestSchema,
) -> AdminUserRead:
    ensure_admin_user(current_user)
    existing_user = identity_user_database_client.get_user_by_id(db, user_id=user_id)
    if existing_user is None:
        raise UserNotFoundError()

    try:
        user = identity_user_database_client.update_user_fields(
            db,
            user_id=user_id,
            is_active=payload.is_active,
            api_access_enabled=payload.api_access_enabled,
        )
        db.commit()
    except Exception:
        db.rollback()
        raise

    return _build_admin_user_read(user)


def _build_admin_user_read(user: UserRecord) -> AdminUserRead:
    return AdminUserRead(
        id=user.id,
        email=user.email,
        pseudo=user.pseudo,
        role=user.role,
        is_active=user.is_active,
        api_access_enabled=user.api_access_enabled,
    )
