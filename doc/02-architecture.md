# Architecture

## High-Level Layers

- `app/main.py`: application bootstrap, logging, middleware, and router registration
- `app/database.py`: DB URL resolution, engine creation, and session factories
- `app/routers`: thin admin HTTP route layer
- `app/services`: orchestration layer for admin workflows
- `app/clients/database`: RSS SQL operations and admin counters
- `app/clients/networking`: upstream HTTP clients and Redis low-level client
- `app/domain`: RSS normalization and lock helpers

## Route Layer

Main route families:

- `/internal/health`: simple liveness endpoint
- `/internal/admin/health/`: detailed dependency health
- `/internal/admin/stats`: aggregated admin statistics
- `/internal/admin/users...`: user administration delegated to `user_service`
- `/internal/admin/jobs...`: job and automation operations delegated to `worker_service`
- `/internal/admin/rss...`: RSS read and mutation endpoints

## Business Layer

Key service modules:

- `app/services/admin_stats_service.py`
- `app/services/admin_users_service.py`
- `app/services/jobs_service.py`
- `app/services/rss_sync_service.py`
- `app/services/rss_toggle_service.py`

These modules keep the route layer thin and isolate orchestration concerns from
FastAPI request handling.

## Persistence Layer

Database responsibilities are split by concern:

- `app/database.py`: content and identity DB sessions
- `app/clients/database/rss_*`: RSS catalog and runtime SQL operations
- `app/clients/database/source_stats_database_client.py`: content-side admin counters
- `app/clients/database/auth_database_client.py`: identity-side admin counters

## Upstream Dependency Layer

Delegated HTTP integrations are isolated in:

- `app/clients/networking/service_http_client.py`
- `app/clients/networking/user_service_networking_client.py`
- `app/clients/networking/worker_service_networking_client.py`

This keeps upstream URL resolution, internal token propagation, timeout
handling, and error mapping in one place.

## Error and Schema Strategy

- Shared contracts, exceptions, and handlers are imported directly from
  `shared_backend`
- Service-local schemas remain only when they contain worker- or API-specific
  behavior
