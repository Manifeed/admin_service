from fastapi import APIRouter, Body, Depends, Path, Query

from app.internal.security import require_internal_service_token
from app.schemas.jobs.job_automation_schema import (
    JobAutomationRead,
    JobAutomationUpdateRequestSchema,
)
from app.schemas.jobs.job_enqueue_schema import (
    JobEnqueueRead,
    RssScrapeJobCreateRequestSchema,
    SourceEmbeddingJobCreateRequestSchema,
)
from app.schemas.jobs.job_schema import JobStatusRead, JobTaskRead, JobsOverviewRead
from app.services import jobs_service


jobs_router = APIRouter(
    prefix="/internal/admin/jobs",
    tags=["internal-admin-jobs"],
    dependencies=[Depends(require_internal_service_token)],
)


@jobs_router.get("", response_model=JobsOverviewRead)
def read_jobs_overview(limit: int = Query(default=100, ge=1, le=500)) -> JobsOverviewRead:
    return jobs_service.list_jobs(limit=limit)


@jobs_router.post("/rss-scrape", response_model=JobEnqueueRead)
def create_rss_scrape_job(
    payload: RssScrapeJobCreateRequestSchema | None = Body(default=None),
) -> JobEnqueueRead:
    return jobs_service.enqueue_rss_scrape_job(payload)


@jobs_router.post("/source-embedding", response_model=JobEnqueueRead)
def create_source_embedding_job(
    payload: SourceEmbeddingJobCreateRequestSchema | None = Body(default=None),
) -> JobEnqueueRead:
    return jobs_service.enqueue_source_embedding_job(payload)


@jobs_router.get("/automation", response_model=JobAutomationRead)
def read_job_automation_route() -> JobAutomationRead:
    return jobs_service.read_job_automation()


@jobs_router.patch("/automation", response_model=JobAutomationRead)
def update_job_automation_route(payload: JobAutomationUpdateRequestSchema) -> JobAutomationRead:
    return jobs_service.update_job_automation(payload)


@jobs_router.get("/{job_id}/tasks", response_model=list[JobTaskRead])
def read_job_tasks(job_id: str = Path(min_length=1)) -> list[JobTaskRead]:
    return jobs_service.list_job_tasks(job_id=job_id)


@jobs_router.get("/{job_id}", response_model=JobStatusRead)
def read_job_status(job_id: str = Path(min_length=1)) -> JobStatusRead:
    return jobs_service.read_job_status(job_id=job_id)
