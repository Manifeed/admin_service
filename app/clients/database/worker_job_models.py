from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


QUEUE_NAME_RSS_SCRAPE_REQUESTS = "rss.fetch"
QUEUE_NAME_SOURCE_EMBEDDING_REQUESTS = "embed.source"

TASK_KIND_RSS_SCRAPE = "rss_scrape"
TASK_KIND_SOURCE_EMBEDDING = "source_embedding"

WORKER_TYPE_RSS_SCRAPPER = "rss_scrapper"
WORKER_TYPE_SOURCE_EMBEDDING = "source_embedding"


@dataclass(frozen=True)
class WorkerJobTaskClaimRow:
    task_id: int
    execution_id: int
    job_id: str
    requested_at: datetime
    ref_ids: list[int]
    worker_version: str | None
    task_type: str
    item_total: int


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
