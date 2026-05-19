from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class WorkerJobRecord:
    job_id: str
    job_kind: str
    task_type: str
    worker_version: str | None
    requested_at: datetime
    started_at: datetime | None
    finished_at: datetime | None
    finalized_at: datetime | None
    status: str
    task_total: int
    task_processed: int
    item_total: int
    item_success: int
    item_error: int


@dataclass(frozen=True)
class WorkerJobProgressSnapshot:
    task_total: int
    task_processed: int
    item_success: int
    item_error: int
    processing_count: int
    pending_count: int
    cancelled_count: int
