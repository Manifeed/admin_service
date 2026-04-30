from __future__ import annotations

from sqlalchemy.orm import Session

from app.auth.database.auth_database_client import count_connected_users, count_users
from shared_backend.schemas.admin.admin_stats_schema import AdminStatsRead
from app.sources.database.get_sources_db_cli import count_sources


def read_admin_stats(
    identity_db: Session,
    content_db: Session,
) -> AdminStatsRead:
    return AdminStatsRead(
        connected_users=count_connected_users(identity_db),
        total_users=count_users(identity_db),
        connected_workers=0,
        total_sources=count_sources(content_db),
    )
