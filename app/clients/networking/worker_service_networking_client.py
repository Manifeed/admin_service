from __future__ import annotations

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from shared_backend.schemas.internal.worker_service_schema import WorkerServiceStatsRead


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

def get_worker_service_client() -> WorkerServiceNetworkingClient | None:
    return WorkerServiceNetworkingClient.from_env()


def get_required_worker_service_client() -> WorkerServiceNetworkingClient:
    return require_service_client(
        get_worker_service_client(),
        env_name="WORKER_SERVICE_URL",
    )
