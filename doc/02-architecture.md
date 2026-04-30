# Architecture

## High-Level Layers

- `main.py`: application bootstrap, logging, middleware, and router registration
- `database.py`: DB URL resolution, engine creation, and session factories
- `app/internal`: internal security and admin stats route layer
- `app/health`: dependency health probing for Postgres, Redis, and Qdrant
- `app/routers`: delegated admin user and admin job HTTP routes
- `app/services`: business layer for delegated user/job operations
- `app/rss`: RSS read, sync, toggle, and repository logic
- `app/analytics`: analysis overview and similar-source reads
- `app/clients/networking`: upstream HTTP clients and Redis low-level client

## Route Layer

Main route families:

- `/internal/health`: simple liveness endpoint
- `/internal/admin/health/`: detailed dependency health
- `/internal/admin/stats`: aggregated admin statistics
- `/internal/admin/users...`: user administration delegated to `user_service`
- `/internal/admin/jobs...`: job and automation operations delegated to `worker_service`
- `/internal/admin/rss...`: RSS read and mutation endpoints
- `/internal/admin/analysis...`: analysis overview and similar-source reads

## Business Layer

Key service modules:

- `app/admin/services/admin_stats_service.py`
- `app/services/admin_users_service.py`
- `app/services/jobs_service.py`
- `app/rss/services/rss_sync_service.py`
- `app/rss/services/rss_toggle_service.py`
- `app/analytics/services/analysis_service.py`

These modules keep the route layer thin and isolate orchestration concerns from
FastAPI request handling.

## Persistence Layer

Database responsibilities are split by concern:

- `database.py`: content and identity DB sessions
- `app/rss/database/*`: RSS catalog and runtime SQL operations
- `app/sources/database/*`: source and embedding-related read models
- `app/auth/database/auth_database_client.py`: identity-side admin counters

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
