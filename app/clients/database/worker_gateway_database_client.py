from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.orm import Session


def count_active_worker_sessions(db: Session, *, worker_type: str | None = None) -> int:
    filters = ["expires_at >= now()"]
    params: dict[str, object] = {}
    if worker_type:
        filters.append("worker_type = :worker_type")
        params["worker_type"] = worker_type
    return int(
        db.execute(
            text(
                """
                SELECT COUNT(*)
                FROM worker_sessions
                WHERE """
                + " AND ".join(filters)
            ),
            params,
        ).scalar_one()
        or 0
    )
