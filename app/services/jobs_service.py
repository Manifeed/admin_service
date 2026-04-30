from __future__ import annotations

from app.clients.networking.worker_service_networking_client import (
    get_required_worker_service_client,
)
from shared_backend.schemas.jobs.job_automation_schema import (
    JobAutomationRead,
    JobAutomationUpdateRequestSchema,
)
from shared_backend.schemas.jobs.job_enqueue_schema import (
    JobEnqueueRead,
    RssScrapeJobCreateRequestSchema,
    SourceEmbeddingJobCreateRequestSchema,
)
from shared_backend.schemas.jobs.job_schema import JobStatusRead, JobTaskRead, JobsOverviewRead


def list_jobs(*, limit: int) -> JobsOverviewRead:
    return get_required_worker_service_client().list_jobs(limit=limit)


def enqueue_rss_scrape_job(
    payload: RssScrapeJobCreateRequestSchema | None,
) -> JobEnqueueRead:
    return get_required_worker_service_client().enqueue_rss_scrape_job(payload)


def enqueue_source_embedding_job(
    payload: SourceEmbeddingJobCreateRequestSchema | None,
) -> JobEnqueueRead:
    return get_required_worker_service_client().enqueue_source_embedding_job(payload)


def read_job_automation() -> JobAutomationRead:
    return get_required_worker_service_client().read_job_automation()


def update_job_automation(
    payload: JobAutomationUpdateRequestSchema,
) -> JobAutomationRead:
    return get_required_worker_service_client().update_job_automation(payload)


def list_job_tasks(*, job_id: str) -> list[JobTaskRead]:
    return get_required_worker_service_client().list_job_tasks(job_id=job_id)


def read_job_status(*, job_id: str) -> JobStatusRead:
    return get_required_worker_service_client().read_job_status(job_id=job_id)
