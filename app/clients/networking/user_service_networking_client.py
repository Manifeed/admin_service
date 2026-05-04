from __future__ import annotations

from app.clients.networking.service_http_client import require_service_client

from shared_backend.clients.user_service_networking_client import (
    INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER,
    INTERNAL_CURRENT_USER_EMAIL_HEADER,
    INTERNAL_CURRENT_USER_ID_HEADER,
    INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER,
    INTERNAL_CURRENT_USER_ROLE_HEADER,
    INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER,
    UserServiceNetworkingClient,
)


def get_user_service_client() -> UserServiceNetworkingClient | None:
    return UserServiceNetworkingClient.from_env()


def get_required_user_service_client() -> UserServiceNetworkingClient:
    return require_service_client(
        get_user_service_client(),
        env_name="USER_SERVICE_URL",
    )


__all__ = [
    "INTERNAL_CURRENT_USER_API_ACCESS_ENABLED_HEADER",
    "INTERNAL_CURRENT_USER_EMAIL_HEADER",
    "INTERNAL_CURRENT_USER_ID_HEADER",
    "INTERNAL_CURRENT_USER_IS_ACTIVE_HEADER",
    "INTERNAL_CURRENT_USER_ROLE_HEADER",
    "INTERNAL_CURRENT_USER_SESSION_EXPIRES_AT_HEADER",
    "UserServiceNetworkingClient",
    "get_required_user_service_client",
    "get_user_service_client",
]
