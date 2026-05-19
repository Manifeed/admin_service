from __future__ import annotations

import httpx

from app.clients.networking import worker_service_networking_client
from app.clients.networking.worker_service_networking_client import WorkerServiceNetworkingClient
from app.clients.networking.service_http_client import ServiceClientConfig
from shared_backend.schemas.internal.worker_service_schema import WorkerServiceStatsRead


def _config() -> ServiceClientConfig:
    return ServiceClientConfig(
        base_url="http://worker-service:8000",
        internal_token="x" * 32,
        timeout_seconds=10.0,
        service_name="Worker",
    )


def test_read_worker_stats_uses_internal_worker_stats_endpoint(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={
                "connected_workers": 2,
                "pending_rss_tasks": 1,
                "pending_embedding_tasks": 3,
                "expired_claims": 0,
                "stale_redis_task_ids_dropped": 0,
                "embedding_tasks_requeued": 0,
                "payload_rebuild_failures": 0,
            },
            request=httpx.Request("GET", "http://worker-service:8000/internal/workers/stats"),
        )

    monkeypatch.setattr(worker_service_networking_client, "request_service", fake_request_service)
    client = WorkerServiceNetworkingClient(_config())

    response = client.read_worker_stats()

    assert isinstance(response, WorkerServiceStatsRead)
    assert response.connected_workers == 2
    assert seen["path"] == "/internal/workers/stats"
