from __future__ import annotations

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from app.schemas.internal.worker_service_schema import WorkerServiceStatsRead
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


class WorkerServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "WorkerServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="WORKER_SERVICE_URL",
            timeout_env="WORKER_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=10.0,
            service_name="Worker",
        )
        if config is None:
            return None
        return cls(config)

    def read_worker_stats(self) -> WorkerServiceStatsRead:
        response = request_service(
            config=self._config,
            method="GET",
            path="/internal/workers/stats",
            http_client=self._http_client,
        )
        return WorkerServiceStatsRead.model_validate(response.json())

    def list_jobs(self, *, limit: int) -> JobsOverviewRead:
        response = request_service(
            config=self._config,
            method="GET",
            path="/internal/jobs",
            params={"limit": limit},
            http_client=self._http_client,
        )
        return JobsOverviewRead.model_validate(response.json())

    def enqueue_rss_scrape_job(
        self,
        payload: RssScrapeJobCreateRequestSchema | None,
    ) -> JobEnqueueRead:
        response = request_service(
            config=self._config,
            method="POST",
            path="/internal/jobs/rss-scrape",
            json=(payload.model_dump(mode="json") if payload is not None else None),
            http_client=self._http_client,
        )
        return JobEnqueueRead.model_validate(response.json())

    def enqueue_source_embedding_job(
        self,
        payload: SourceEmbeddingJobCreateRequestSchema | None,
    ) -> JobEnqueueRead:
        response = request_service(
            config=self._config,
            method="POST",
            path="/internal/jobs/source-embedding",
            json=(payload.model_dump(mode="json") if payload is not None else None),
            http_client=self._http_client,
        )
        return JobEnqueueRead.model_validate(response.json())

    def read_job_automation(self) -> JobAutomationRead:
        response = request_service(
            config=self._config,
            method="GET",
            path="/internal/jobs/automation",
            http_client=self._http_client,
        )
        return JobAutomationRead.model_validate(response.json())

    def update_job_automation(
        self,
        payload: JobAutomationUpdateRequestSchema,
    ) -> JobAutomationRead:
        response = request_service(
            config=self._config,
            method="PATCH",
            path="/internal/jobs/automation",
            json=payload.model_dump(mode="json"),
            http_client=self._http_client,
        )
        return JobAutomationRead.model_validate(response.json())

    def list_job_tasks(self, *, job_id: str) -> list[JobTaskRead]:
        response = request_service(
            config=self._config,
            method="GET",
            path=f"/internal/jobs/{job_id}/tasks",
            http_client=self._http_client,
        )
        return [JobTaskRead.model_validate(item) for item in response.json()]

    def read_job_status(self, *, job_id: str) -> JobStatusRead:
        response = request_service(
            config=self._config,
            method="GET",
            path=f"/internal/jobs/{job_id}",
            http_client=self._http_client,
        )
        return JobStatusRead.model_validate(response.json())

def get_worker_service_client() -> WorkerServiceNetworkingClient | None:
    return WorkerServiceNetworkingClient.from_env()


def get_required_worker_service_client() -> WorkerServiceNetworkingClient:
    return require_service_client(
        get_worker_service_client(),
        env_name="WORKER_SERVICE_URL",
    )
