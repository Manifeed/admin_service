from __future__ import annotations

from time import perf_counter
import os
from urllib.parse import urlparse

import httpx
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.clients.networking.redis_networking_client import (
    DEFAULT_REDIS_URL,
    RedisCommandError,
    RedisConnectionConfig,
    RedisNetworkingClient,
)
from shared_backend.schemas.health import HealthRead, HealthServiceRead

HEALTH_TIMEOUT_SECONDS = 2.0
DEFAULT_QDRANT_URL = "http://qdrant:6333"
DEFAULT_QDRANT_COLLECTION = "article_embeddings"


def get_health_status(
    content_db: Session,
    identity_db: Session | None = None,
) -> HealthRead:
    services: dict[str, HealthServiceRead] = {
        "content_postgres": _check_postgres_service(content_db, "content_postgres"),
    }
    if identity_db is not None:
        services["identity_postgres"] = _check_postgres_service(
            identity_db,
            "identity_postgres",
        )
    services["qdrant"] = _check_qdrant_service()
    services["redis"] = _check_redis_service()

    postgres_services = [
        service
        for service_key, service in services.items()
        if service_key.endswith("_postgres")
    ]
    postgres_available = all(service.status == "ok" for service in postgres_services)
    overall_status = "ok" if all(service.status == "ok" for service in services.values()) else "degraded"
    return HealthRead(
        status=overall_status,
        database="ok" if postgres_available else "unavailable",
        services=services,
    )


def _check_postgres_service(db: Session, name: str) -> HealthServiceRead:
    started_at = perf_counter()
    try:
        database_name = db.execute(text("SELECT current_database()")).scalar_one_or_none()
        return HealthServiceRead(
            name=name,
            kind="postgres",
            status="ok",
            detail=_health_detail(
                f"database={database_name}"
                if isinstance(database_name, str) and database_name.strip()
                else None
            ),
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except Exception as exception:
        return HealthServiceRead(
            name=name,
            kind="postgres",
            status="unavailable",
            detail=_health_error_detail(exception),
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _check_qdrant_service() -> HealthServiceRead:
    base_url = _resolve_qdrant_url()
    collection_name = _resolve_qdrant_collection_name()
    started_at = perf_counter()
    try:
        with httpx.Client(timeout=HEALTH_TIMEOUT_SECONDS) as http_client:
            response = http_client.get(
                f"{base_url}/collections",
                headers=_build_qdrant_headers(),
            )
        if response.status_code >= 400:
            raise RuntimeError(f"HTTP {response.status_code}")
        return HealthServiceRead(
            name="qdrant",
            kind="qdrant",
            status="ok",
            detail=_health_detail(f"collection={collection_name}"),
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except Exception as exception:
        return HealthServiceRead(
            name="qdrant",
            kind="qdrant",
            status="unavailable",
            detail=_health_error_detail(exception),
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _check_redis_service() -> HealthServiceRead:
    started_at = perf_counter()
    try:
        redis_url = os.getenv("REDIS_URL", DEFAULT_REDIS_URL).strip() or DEFAULT_REDIS_URL
        client = RedisNetworkingClient(
            RedisConnectionConfig(
                url=redis_url,
                timeout_seconds=HEALTH_TIMEOUT_SECONDS,
            )
        )
        parsed_url = urlparse(client.config.url)
        host = parsed_url.hostname or "localhost"
        port = parsed_url.port or 6379
        db_index = parsed_url.path.lstrip("/") or "0"
        ping_response = client.ping()
        if ping_response != "PONG":
            raise RuntimeError(f"Unexpected Redis ping response: {ping_response}")
        return HealthServiceRead(
            name="redis",
            kind="redis",
            status="ok",
            detail=_health_detail(f"db={db_index} host={host}:{port}"),
            latency_ms=_elapsed_milliseconds(started_at),
        )
    except (RedisCommandError, RuntimeError) as exception:
        return HealthServiceRead(
            name="redis",
            kind="redis",
            status="unavailable",
            detail=_health_error_detail(exception),
            latency_ms=_elapsed_milliseconds(started_at),
        )


def _health_detail(value: str | None) -> str | None:
    if _include_health_details():
        return value
    return None


def _health_error_detail(exception: Exception) -> str:
    if _include_health_details():
        return str(exception)
    if isinstance(exception, TimeoutError):
        return "timeout"
    if isinstance(exception, OSError):
        return "connection_failed"
    return "unavailable"


def _include_health_details() -> bool:
    raw_value = os.getenv("HEALTH_INCLUDE_DETAILS")
    if raw_value is not None:
        return raw_value.strip().lower() in {"1", "true", "yes", "on"}
    environment = " ".join(
        os.getenv(env_var, "")
        for env_var in ("APP_ENV", "ENVIRONMENT", "NODE_ENV")
    ).lower()
    return not any(value in environment for value in ("prod", "production", "staging"))


def _elapsed_milliseconds(started_at: float) -> int:
    return max(0, round((perf_counter() - started_at) * 1000))


def _resolve_qdrant_url() -> str:
    return os.getenv("QDRANT_URL", DEFAULT_QDRANT_URL).rstrip("/")


def _resolve_qdrant_collection_name() -> str:
    return os.getenv("QDRANT_COLLECTION_NAME", DEFAULT_QDRANT_COLLECTION).strip() or DEFAULT_QDRANT_COLLECTION


def _build_qdrant_headers() -> dict[str, str]:
    api_key = os.getenv("QDRANT_API_KEY", "").strip()
    return {"api-key": api_key} if api_key else {}
