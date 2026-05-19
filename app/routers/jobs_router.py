from typing import Annotated

from fastapi import APIRouter, Body, Depends, Path, Query
from sqlalchemy.orm import Session

from app.database import (
    get_content_read_db_session,
    get_workers_read_db_session,
    get_workers_write_db_session,
)
from shared_backend.security.internal_service_auth import require_internal_service_token
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
from app.services import jobs_service


jobs_router = APIRouter(
    prefix="/internal/admin/jobs",
    tags=["internal-admin-jobs"],
    dependencies=[Depends(require_internal_service_token)],
)


@jobs_router.get("", response_model=JobsOverviewRead)
def read_jobs_overview(
    limit: int = Query(default=100, ge=1, le=500),
    workers_db: Session = Depends(get_workers_read_db_session),
) -> JobsOverviewRead:
    return jobs_service.list_jobs(workers_db=workers_db, limit=limit)


@jobs_router.post("/rss-scrape", response_model=JobEnqueueRead)
def create_rss_scrape_job(
    payload: Annotated[RssScrapeJobCreateRequestSchema | None, Body(embed=True)] = None,
    content_db: Session = Depends(get_content_read_db_session),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobEnqueueRead:
    return jobs_service.enqueue_rss_scrape_job(content_db, workers_db, payload)


@jobs_router.post("/source-embedding", response_model=JobEnqueueRead)
def create_source_embedding_job(
    payload: Annotated[SourceEmbeddingJobCreateRequestSchema | None, Body(embed=True)] = None,
    content_db: Session = Depends(get_content_read_db_session),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobEnqueueRead:
    return jobs_service.enqueue_source_embedding_job(content_db, workers_db, payload)


@jobs_router.get("/automation", response_model=JobAutomationRead)
def read_job_automation_route(
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobAutomationRead:
    return jobs_service.read_job_automation(workers_db=workers_db)


@jobs_router.patch("/automation", response_model=JobAutomationRead)
def update_job_automation_route(
    payload: Annotated[JobAutomationUpdateRequestSchema, Body(embed=True)],
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobAutomationRead:
    return jobs_service.update_job_automation(workers_db=workers_db, payload=payload)


@jobs_router.get("/{job_id}/tasks", response_model=list[JobTaskRead])
def read_job_tasks(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_read_db_session),
) -> list[JobTaskRead]:
    return jobs_service.list_job_tasks(workers_db=workers_db, job_id=job_id)


@jobs_router.get("/{job_id}", response_model=JobStatusRead)
def read_job_status(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_read_db_session),
) -> JobStatusRead:
    return jobs_service.read_job_status(workers_db=workers_db, job_id=job_id)


@jobs_router.post("/{job_id}/pause", response_model=JobStatusRead)
def pause_job_route(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobStatusRead:
    return jobs_service.pause_job(workers_db=workers_db, job_id=job_id)


@jobs_router.post("/{job_id}/resume", response_model=JobStatusRead)
def resume_job_route(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobStatusRead:
    return jobs_service.resume_job(workers_db=workers_db, job_id=job_id)


@jobs_router.post("/{job_id}/cancel", response_model=JobStatusRead)
def cancel_job_route(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobStatusRead:
    return jobs_service.cancel_job(workers_db=workers_db, job_id=job_id)


@jobs_router.delete("/{job_id}", response_model=JobControlCommandRead)
def delete_job_route(
    job_id: str = Path(min_length=1),
    workers_db: Session = Depends(get_workers_write_db_session),
) -> JobControlCommandRead:
    return jobs_service.delete_job(workers_db=workers_db, job_id=job_id)
