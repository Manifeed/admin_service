# Manifeed Admin Service

`admin_service` is the internal administration service for Manifeed.
It exposes backend-only FastAPI endpoints for admin dashboards, RSS catalog
administration, analysis reads, and delegated calls to `user_service` and
`worker_service`.

This service is intended for trusted internal consumers such as `public_api`,
not for browsers or public clients directly.

## What This Service Provides

- Admin statistics aggregation
- Detailed dependency health reporting
- RSS catalog listing and synchronization
- RSS company and feed enable/disable operations
- Analysis overview and similar-source lookup
- Delegation of admin user management to `user_service`
- Delegation of job and automation operations to `worker_service`
- Internal token gate (`x-manifeed-internal-token`) on admin routes

## Architecture Overview

- `app/internal`: internal auth helpers and admin stats routes
- `app/health`: dependency-aware health endpoint
- `app/routers`: admin user and job HTTP routes
- `app/services`: delegated user/job business layer
- `app/rss`: RSS domain, SQL clients, sync workflow, and toggles
- `app/analytics`: analysis overview and Qdrant-backed similarity routes
- `app/clients/networking`: HTTP clients for upstream services + Redis client
- `shared_backend`: shared schemas, inter-service auth helpers, and HTTP client primitives
- `database.py`: SQLAlchemy engines and DB session factories

## Quick Start (Local Development)

### 1) Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2) Set a minimal local environment

```bash
export APP_ENV=local
export CONTENT_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_content
export IDENTITY_DATABASE_URL=postgresql://manifeed:manifeed@localhost:5432/manifeed_identity
export USER_SERVICE_URL=http://localhost:8002
export WORKER_SERVICE_URL=http://localhost:8003
```

Optional dependencies:

```bash
export REDIS_URL=redis://localhost:6379/0
export QDRANT_URL=http://localhost:6333
export RSS_FEEDS_REPOSITORY_PATH=var/rss_feeds
```

### 3) Run the API

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Service endpoints include:

- `GET /internal/health`
- `GET /internal/admin/health/`
- `GET /internal/admin/stats`
- `GET/PATCH /internal/admin/users...`
- `GET/POST/PATCH /internal/admin/jobs...`
- `GET/PATCH/POST /internal/admin/rss...`
- `GET /internal/admin/analysis/...`

## Security Model

- All admin routers rely on `x-manifeed-internal-token` authorization.
- Local/test-like environments may allow missing token when not explicitly
  forced into strict mode.
- Token comparison uses constant-time `secrets.compare_digest`.
- RSS mutations are serialized through DB-backed job locking.
- CSRF origin checks are present for `/api/*` unsafe methods, although this
  service primarily exposes internal routes.

## Configuration

### Core runtime

- `APP_ENV` / `ENVIRONMENT` / `NODE_ENV`: environment resolution
- `CONTENT_DATABASE_URL`: content Postgres DSN
- `IDENTITY_DATABASE_URL`: identity Postgres DSN
- `DATABASE_URL`: fallback for `CONTENT_DATABASE_URL`
- `REQUIRE_EXPLICIT_DATABASE_URLS`: require explicit DB URLs in strict envs
- `INTERNAL_SERVICE_TOKEN`: shared internal authorization secret
- `REQUIRE_INTERNAL_SERVICE_TOKEN`: force strict internal token mode

### Upstream services

- `USER_SERVICE_URL`: base URL for `user_service`
- `USER_SERVICE_TIMEOUT_SECONDS`: user service request timeout
- `WORKER_SERVICE_URL`: base URL for `worker_service`
- `WORKER_SERVICE_TIMEOUT_SECONDS`: worker service request timeout

### Admin health and dependency checks

- `REDIS_URL`: Redis connection URL
- `REDIS_SOCKET_TIMEOUT_SECONDS`: Redis socket timeout
- `QDRANT_URL`: Qdrant base URL
- `QDRANT_COLLECTION_NAME`: Qdrant collection name
- `QDRANT_API_KEY`: optional Qdrant API key
- `HEALTH_INCLUDE_DETAILS`: expose dependency details in health responses

### RSS catalog sync

- `RSS_FEEDS_REPOSITORY_URL`: Git repository used for RSS catalog sync
- `RSS_FEEDS_REPOSITORY_BRANCH`: branch to track
- `RSS_FEEDS_REPOSITORY_PATH`: local clone path

### HTTP / browser-related settings

- `CORS_ORIGINS`: allowed origins for CORS
- `CSRF_TRUSTED_ORIGINS`: explicit trusted origins for unsafe `/api/*` calls
- `CSRF_TRUST_SELF_ORIGIN`: trust request self-origin outside strict envs

### DB pool tuning

- `DB_POOL_SIZE`: SQLAlchemy pool size (`20`)
- `DB_MAX_OVERFLOW`: SQLAlchemy max overflow (`40`)
- `DB_POOL_TIMEOUT_SECONDS`: pool checkout timeout (`30`)
- `DB_POOL_RECYCLE_SECONDS`: pool recycle interval (`1800`)

## Tests

Run the current test suite:

```bash
pytest -q
```

Current tests are limited and mainly cover source compilation.

## Docker

Build from the monorepo root:

```bash
docker build -t manifeed-admin-service -f admin_service/Dockerfile .
```

Run:

```bash
docker run --rm -p 8000:8000 \
	-e APP_ENV=production \
	-e CONTENT_DATABASE_URL='postgresql://user:pass@content-host:5432/content' \
	-e IDENTITY_DATABASE_URL='postgresql://user:pass@identity-host:5432/identity' \
	-e USER_SERVICE_URL='http://user-service:8000' \
	-e WORKER_SERVICE_URL='http://worker-service:8000' \
	-e INTERNAL_SERVICE_TOKEN='replace-with-strong-secret-min-32-chars' \
	manifeed-admin-service
```

The runtime image is multi-stage, runs as a non-root user, and installs
`shared_backend` from a wheel built locally from the monorepo.

## Detailed Documentation

Documentation is available in:

- `doc/README.md`
