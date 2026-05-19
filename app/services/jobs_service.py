from __future__ import annotations

from sqlalchemy.orm import Session

from app.services.admin_job_automation_service import read_job_automation as read_job_automation_from_storage
from app.services.admin_job_automation_service import update_job_automation as update_job_automation_in_storage
from app.services.job_control_service import (
    cancel_job as cancel_job_in_storage,
    delete_job_permanently,
    pause_job as pause_job_in_storage,
    resume_job as resume_job_in_storage,
)
from app.services.job_enqueue_service import (
    enqueue_rss_scrape_job as enqueue_rss_scrape_job_in_storage,
    enqueue_source_embedding_job as enqueue_source_embedding_job_in_storage,
)
from app.services.job_read_service import (
    get_job_status,
    list_job_tasks as list_job_tasks_from_storage,
    list_jobs as list_jobs_from_storage,
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
from shared_backend.schemas.jobs.job_schema import (
    JobControlCommandRead,
    JobStatusRead,
    JobTaskRead,
    JobsOverviewRead,
)


def list_jobs(*, workers_db: Session, limit: int) -> JobsOverviewRead:
    return list_jobs_from_storage(workers_db, limit=limit)


def enqueue_rss_scrape_job(
    content_db: Session,
    workers_db: Session,
    payload: RssScrapeJobCreateRequestSchema | None,
) -> JobEnqueueRead:
    normalized_payload = payload or RssScrapeJobCreateRequestSchema()
    return enqueue_rss_scrape_job_in_storage(
        content_db,
        workers_db,
        feed_ids=normalized_payload.feed_ids or None,
    )


def enqueue_source_embedding_job(
    content_db: Session,
    workers_db: Session,
    payload: SourceEmbeddingJobCreateRequestSchema | None,
) -> JobEnqueueRead:
    normalized_payload = payload or SourceEmbeddingJobCreateRequestSchema()
    return enqueue_source_embedding_job_in_storage(
        content_db,
        workers_db,
        reembed_model_mismatches=normalized_payload.reembed_model_mismatches,
        force_reindex_all=normalized_payload.force_reindex_all,
    )


def read_job_automation(*, workers_db: Session) -> JobAutomationRead:
    return read_job_automation_from_storage(workers_db)


def update_job_automation(
    *,
    workers_db: Session,
    payload: JobAutomationUpdateRequestSchema,
) -> JobAutomationRead:
    return update_job_automation_in_storage(workers_db, payload)


def list_job_tasks(*, workers_db: Session, job_id: str) -> list[JobTaskRead]:
    return list_job_tasks_from_storage(workers_db, job_id=job_id)


def read_job_status(*, workers_db: Session, job_id: str) -> JobStatusRead:
    return get_job_status(workers_db, job_id=job_id)


def pause_job(*, workers_db: Session, job_id: str) -> JobStatusRead:
    return pause_job_in_storage(workers_db, job_id=job_id)


def resume_job(*, workers_db: Session, job_id: str) -> JobStatusRead:
    return resume_job_in_storage(workers_db, job_id=job_id)


def cancel_job(*, workers_db: Session, job_id: str) -> JobStatusRead:
    return cancel_job_in_storage(workers_db, job_id=job_id)


def delete_job(*, workers_db: Session, job_id: str) -> JobControlCommandRead:
    return delete_job_permanently(workers_db, job_id=job_id)
