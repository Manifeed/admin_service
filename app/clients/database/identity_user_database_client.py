from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass(frozen=True)
class UserRecord:
    id: int
    email: str
    pseudo: str
    pp_id: int
    password_hash: str
    role: str
    is_active: bool
    api_access_enabled: bool
    created_at: datetime
    updated_at: datetime


def get_user_by_id(db: Session, *, user_id: int) -> UserRecord | None:
    row = (
        db.execute(
            text(
                """
                SELECT
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                FROM users
                WHERE id = :user_id
                """
            ),
            {"user_id": user_id},
        )
        .mappings()
        .one_or_none()
    )
    return _map_user(row) if row is not None else None


def list_users(
    db: Session,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    api_access_enabled: bool | None = None,
    search: str | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[UserRecord], int]:
    where_sql, params = _build_user_filters(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    total = count_users(
        db,
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    if total == 0:
        return [], 0

    rows = (
        db.execute(
            text(
                f"""
                SELECT
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                FROM users
                {where_sql}
                ORDER BY created_at ASC, id ASC
                LIMIT :limit
                OFFSET :offset
                """
            ),
            {
                **params,
                "limit": max(1, min(int(limit), 100)),
                "offset": max(0, int(offset)),
            },
        )
        .mappings()
        .all()
    )
    return [_map_user(row) for row in rows], total


def count_users(
    db: Session,
    *,
    role: str | None = None,
    is_active: bool | None = None,
    api_access_enabled: bool | None = None,
    search: str | None = None,
) -> int:
    where_sql, params = _build_user_filters(
        role=role,
        is_active=is_active,
        api_access_enabled=api_access_enabled,
        search=search,
    )
    return int(
        db.execute(
            text(
                f"""
                SELECT COUNT(*)
                FROM users
                {where_sql}
                """
            ),
            params,
        ).scalar_one()
        or 0
    )


def update_user_fields(
    db: Session,
    *,
    user_id: int,
    is_active: bool | None,
    api_access_enabled: bool | None,
) -> UserRecord:
    set_clauses: list[str] = ["updated_at = now()"]
    params: dict[str, object] = {"user_id": user_id}

    if is_active is not None:
        set_clauses.append("is_active = :is_active")
        params["is_active"] = is_active
    if api_access_enabled is not None:
        set_clauses.append("api_access_enabled = :api_access_enabled")
        params["api_access_enabled"] = api_access_enabled

    row = (
        db.execute(
            text(
                f"""
                UPDATE users
                SET
                    {", ".join(set_clauses)}
                WHERE id = :user_id
                RETURNING
                    id,
                    email,
                    pseudo,
                    pp_id,
                    password_hash,
                    role,
                    is_active,
                    api_access_enabled,
                    created_at,
                    updated_at
                """
            ),
            params,
        )
        .mappings()
        .one()
    )
    return _map_user(row)


def _build_user_filters(
    *,
    role: str | None,
    is_active: bool | None,
    api_access_enabled: bool | None,
    search: str | None,
) -> tuple[str, dict[str, object]]:
    where_clauses: list[str] = []
    params: dict[str, object] = {}

    if role is not None:
        where_clauses.append("role = :role")
        params["role"] = role
    if is_active is not None:
        where_clauses.append("is_active = :is_active")
        params["is_active"] = is_active
    if api_access_enabled is not None:
        where_clauses.append("api_access_enabled = :api_access_enabled")
        params["api_access_enabled"] = api_access_enabled
    if search is not None:
        normalized_search = search.strip()
        if normalized_search:
            where_clauses.append("(email ILIKE :search OR pseudo ILIKE :search)")
            params["search"] = f"%{normalized_search}%"

    if not where_clauses:
        return "", {}
    return f"WHERE {' AND '.join(where_clauses)}", params


def _map_user(row) -> UserRecord:
    return UserRecord(
        id=int(row["id"]),
        email=str(row["email"]),
        pseudo=str(row["pseudo"]),
        pp_id=int(row["pp_id"]),
        password_hash=str(row["password_hash"]),
        role=str(row["role"]),
        is_active=bool(row["is_active"]),
        api_access_enabled=bool(row["api_access_enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )
