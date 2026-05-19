from __future__ import annotations

from datetime import datetime

from sqlalchemy import text
from sqlalchemy.orm import Session


def enqueue_worker_tasks(
    db: Session,
    *,
    job_id: str,
    task_type: str,
    worker_version: str | None,
    requested_at: datetime,
    ref_batches: list[list[int]],
    item_counts: list[int],
) -> list[int]:
    if not ref_batches:
        return []
    if len(ref_batches) != len(item_counts):
        raise ValueError("ref_batches and item_counts length mismatch")
    task_ids: list[int] = []
    for ref_batch, item_count in zip(ref_batches, item_counts, strict=True):
        normalized_ref_ids = [int(value) for value in ref_batch if int(value) > 0]
        if not normalized_ref_ids:
            raise ValueError("worker task ref batch cannot be empty")
        task_id = db.execute(
            text(
                """
                INSERT INTO worker_tasks (
                    job_id,
                    task_type,
                    worker_version,
                    ref_ids,
                    requested_at,
                    status,
                    attempt_count,
                    item_total,
                    item_success,
                    item_error
                ) VALUES (
                    :job_id,
                    :task_type,
                    :worker_version,
                    CAST(:ref_ids AS BIGINT[]),
                    :requested_at,
                    'pending',
                    0,
                    :item_total,
                    0,
                    0
                )
                RETURNING task_id
                """
            ),
            {
                "job_id": job_id,
                "task_type": task_type,
                "worker_version": worker_version,
                "ref_ids": normalized_ref_ids,
                "requested_at": requested_at,
                "item_total": max(1, int(item_count)),
            },
        ).scalar_one()
        task_ids.append(int(task_id))
    return task_ids
