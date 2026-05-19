from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def list_worker_job_tasks(db: Session, *, job_id: str) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            text(
                """
                SELECT
                    task_id,
                    NULLIF(execution_id, 0) AS execution_id,
                    status,
                    claimed_at,
                    completed_at,
                    claim_expires_at,
                    attempt_count,
                    last_error,
                    claim_owner,
                    item_total,
                    item_success,
                    item_error
                FROM worker_tasks
                WHERE job_id = :job_id
                ORDER BY task_id ASC
                """
            ),
            {"job_id": job_id},
        )
        .mappings()
        .all()
    )
    return [dict(row) for row in rows]
