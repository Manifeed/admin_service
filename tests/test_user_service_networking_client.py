from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.clients.networking import user_service_networking_client
from app.clients.networking.user_service_networking_client import UserServiceNetworkingClient
from shared_backend.clients.service_http_client import ServiceClientConfig
from shared_backend.domain.current_user import AuthenticatedUserContext
from shared_backend.schemas.admin.admin_user_schema import AdminUserUpdateRequestSchema


def _config() -> ServiceClientConfig:
    return ServiceClientConfig(
        base_url="http://user-service:8000",
        internal_token="x" * 32,
        timeout_seconds=5.0,
        service_name="User",
    )


def _current_user() -> AuthenticatedUserContext:
    return AuthenticatedUserContext(
        user_id=7,
        email="admin@example.com",
        role="admin",
        is_active=True,
        api_access_enabled=True,
        session_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def test_read_admin_users_wraps_current_user_and_filters(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={"items": [], "total": 0, "active_total": 0, "limit": 25, "offset": 10},
            request=httpx.Request("POST", "http://user-service:8000/internal/users/admin/users/list"),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    current_user = _current_user()

    response = client.read_admin_users(
        current_user=current_user,
        role="admin",
        is_active=True,
        api_access_enabled=True,
        search="bob",
        limit=25,
        offset=10,
    )

    assert response.limit == 25
    assert seen["path"] == "/internal/users/admin/users/list"
    assert seen["json"] == {
        "payload": {
            "current_user": {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "api_access_enabled": current_user.api_access_enabled,
                "session_expires_at": current_user.session_expires_at.isoformat(),
            },
            "filters": {
                "role": "admin",
                "is_active": True,
                "api_access_enabled": True,
                "search": "bob",
                "limit": 25,
                "offset": 10,
            },
        }
    }


def test_update_admin_user_wraps_current_user_and_payload(monkeypatch) -> None:
    seen: dict[str, object] = {}

    def fake_request_service(**kwargs) -> httpx.Response:
        seen.update(kwargs)
        return httpx.Response(
            200,
            json={
                "id": 9,
                "email": "user@example.com",
                "pseudo": "user",
                "role": "user",
                "is_active": True,
                "api_access_enabled": False,
            },
            request=httpx.Request("PATCH", "http://user-service:8000/internal/users/admin/users/9"),
        )

    monkeypatch.setattr(user_service_networking_client, "request_service", fake_request_service)
    client = UserServiceNetworkingClient(_config())
    current_user = _current_user()
    payload = AdminUserUpdateRequestSchema(api_access_enabled=False)

    response = client.update_admin_user(current_user=current_user, user_id=9, payload=payload)

    assert response.id == 9
    assert seen["path"] == "/internal/users/admin/users/9"
    assert seen["json"] == {
        "payload": {
            "current_user": {
                "user_id": current_user.user_id,
                "email": current_user.email,
                "role": current_user.role,
                "is_active": current_user.is_active,
                "api_access_enabled": current_user.api_access_enabled,
                "session_expires_at": current_user.session_expires_at.isoformat(),
            },
            "payload": {
                "api_access_enabled": False,
            },
        }
    }
