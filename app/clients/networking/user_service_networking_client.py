from __future__ import annotations

from typing import Any

import httpx

from app.clients.networking.service_http_client import (
    ServiceClientConfig,
    build_service_config,
    request_service,
    require_service_client,
)
from shared_backend.schemas.admin.admin_user_schema import (
    AdminUserListRead,
    AdminUserRead,
    AdminUserUpdateRequestSchema,
)
from shared_backend.schemas.auth.auth_schema import UserRole


class UserServiceNetworkingClient:
    def __init__(
        self,
        config: ServiceClientConfig,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._http_client = http_client

    @classmethod
    def from_env(cls) -> "UserServiceNetworkingClient | None":
        config = build_service_config(
            base_url_env="USER_SERVICE_URL",
            timeout_env="USER_SERVICE_TIMEOUT_SECONDS",
            default_timeout_seconds=5.0,
            service_name="User",
        )
        if config is None:
            return None
        return cls(config)

    def read_admin_users(
        self,
        *,
        role: UserRole | None,
        is_active: bool | None,
        api_access_enabled: bool | None,
        search: str | None,
        limit: int,
        offset: int,
    ) -> AdminUserListRead:
        response = self._get(
            "/internal/users/admin/users",
            params={
                "role": role,
                "is_active": is_active,
                "api_access_enabled": api_access_enabled,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        )
        return AdminUserListRead.model_validate(response.json())

    def update_admin_user(
        self,
        *,
        user_id: int,
        payload: AdminUserUpdateRequestSchema,
    ) -> AdminUserRead:
        response = self._patch(
            f"/internal/users/admin/users/{user_id}",
            json=payload.model_dump(mode="json", exclude_none=True),
        )
        return AdminUserRead.model_validate(response.json())

    def _get(self, path: str, *, params: dict[str, Any]) -> httpx.Response:
        return self._request("GET", path, params=params, json=None)

    def _patch(self, path: str, *, json: dict[str, Any]) -> httpx.Response:
        return self._request("PATCH", path, params=None, json=json)

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None,
        json: dict[str, Any] | None,
    ) -> httpx.Response:
        return request_service(
            config=self._config,
            method=method,
            path=path,
            params=params,
            json=json,
            http_client=self._http_client,
        )


def get_user_service_client() -> UserServiceNetworkingClient | None:
    return UserServiceNetworkingClient.from_env()


def get_required_user_service_client() -> UserServiceNetworkingClient:
    return require_service_client(
        get_user_service_client(),
        env_name="USER_SERVICE_URL",
    )
