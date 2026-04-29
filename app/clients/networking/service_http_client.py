from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Any

import httpx

from app.errors.app_error import AppError, UpstreamServiceError
from app.security import INTERNAL_SERVICE_TOKEN_HEADER


@dataclass(frozen=True)
class ServiceClientConfig:
    base_url: str
    internal_token: str | None
    timeout_seconds: float
    service_name: str


def build_service_config(
    *,
    base_url_env: str,
    timeout_env: str,
    default_timeout_seconds: float,
    service_name: str,
) -> ServiceClientConfig | None:
    base_url = os.getenv(base_url_env, "").strip().rstrip("/")
    if not base_url:
        return None
    return ServiceClientConfig(
        base_url=base_url,
        internal_token=os.getenv("INTERNAL_SERVICE_TOKEN", "").strip() or None,
        timeout_seconds=_resolve_timeout_seconds(timeout_env, default_timeout_seconds),
        service_name=service_name,
    )


def build_internal_headers(config: ServiceClientConfig) -> dict[str, str]:
    headers = {"Content-Type": "application/json"}
    if config.internal_token:
        headers[INTERNAL_SERVICE_TOKEN_HEADER] = config.internal_token
    return headers


def request_service(
    *,
    config: ServiceClientConfig,
    method: str,
    path: str,
    params: dict[str, Any] | None = None,
    json: dict[str, Any] | None = None,
    http_client: httpx.Client | None = None,
) -> httpx.Response:
    try:
        if http_client is not None:
            response = http_client.request(
                method,
                f"{config.base_url}{path}",
                params=_compact_params(params),
                json=json,
                headers=build_internal_headers(config),
            )
        else:
            with httpx.Client(timeout=config.timeout_seconds) as client:
                response = client.request(
                    method,
                    f"{config.base_url}{path}",
                    params=_compact_params(params),
                    json=json,
                    headers=build_internal_headers(config),
                )
    except httpx.HTTPError as exception:
        raise UpstreamServiceError(f"{config.service_name} service is unavailable") from exception
    raise_for_service_error(response, config.service_name)
    return response


def raise_for_service_error(response: httpx.Response, service_name: str) -> None:
    if response.status_code < 400:
        return
    try:
        payload = response.json()
    except ValueError as exception:
        raise UpstreamServiceError(
            f"{service_name} service returned HTTP {response.status_code}"
        ) from exception
    if isinstance(payload, dict):
        raise AppError(
            str(payload.get("message") or f"{service_name} service error"),
            status_code=response.status_code,
            code=str(payload.get("code") or f"{service_name.lower()}_service_error"),
            details=payload.get("details"),
        )
    raise UpstreamServiceError(f"{service_name} service returned HTTP {response.status_code}")


def require_service_client(client: Any | None, *, env_name: str) -> Any:
    if client is None:
        raise UpstreamServiceError(f"{env_name} is not configured")
    return client


def _compact_params(params: dict[str, Any] | None) -> dict[str, Any] | None:
    if params is None:
        return None
    return {key: value for key, value in params.items() if value is not None}


def _resolve_timeout_seconds(env_name: str, default_value: float) -> float:
    raw_value = os.getenv(env_name, str(default_value))
    try:
        parsed = float(raw_value)
    except ValueError:
        return default_value
    return parsed if parsed > 0 else default_value
