# API Reference

## Health Endpoints

### `GET /internal/health`

Simple liveness endpoint.

Response:

```json
{
	"service": "admin-service",
	"status": "ok"
}
```

### `GET /internal/admin/health/`

Detailed admin health endpoint.

Validates:

- content Postgres connectivity
- identity Postgres connectivity
- Qdrant connectivity
- Redis connectivity

Response shape:

```json
{
	"status": "ok",
	"database": "ok",
	"services": {
		"content_postgres": {
			"name": "content_postgres",
			"kind": "postgres",
			"status": "ok",
			"detail": "database=manifeed_content",
			"latency_ms": 4
		}
	}
}
```

## Admin Stats

### `GET /internal/admin/stats`

Returns aggregated admin counters:

- connected users
- total users
- connected workers
- total sources

This endpoint combines local DB reads with a delegated stats read from
`worker_service`.

## Admin Users

All routes below are protected by internal token authorization.

### `GET /internal/admin/users`

Delegates admin user listing to `user_service`.

Supported filters:

- `role`
- `is_active`
- `api_access_enabled`
- `search`
- `limit`
- `offset`

### `PATCH /internal/admin/users/{user_id}`

Delegates admin user updates to `user_service`.

## Admin Jobs

### `GET /internal/admin/jobs`

Delegates recent job overview reads to `worker_service`.

### `POST /internal/admin/jobs/rss-scrape`

Delegates RSS scrape job creation to `worker_service`.

### `POST /internal/admin/jobs/source-embedding`

Delegates source embedding job creation to `worker_service`.

### `GET /internal/admin/jobs/automation`

Reads automation settings from `worker_service`.

### `PATCH /internal/admin/jobs/automation`

Updates automation settings through `worker_service`.

### `GET /internal/admin/jobs/{job_id}`

Reads a single job status from `worker_service`.

### `GET /internal/admin/jobs/{job_id}/tasks`

Reads task-level details for a job from `worker_service`.

## RSS Administration

### `GET /internal/admin/rss/companies`

Lists RSS companies from the content database.

### `GET /internal/admin/rss/`

Lists RSS feeds, optionally filtered by `company_id`.

### `PATCH /internal/admin/rss/feeds/{feed_id}/enabled`

Toggles a feed enabled state.

### `PATCH /internal/admin/rss/companies/{company_id}/enabled`

Toggles a company enabled state.

### `POST /internal/admin/rss/sync`

Synchronizes the RSS catalog from the configured Git repository.

Query parameter:

- `force`: force a full reconciliation even if the revision did not change

Behavior:

1. acquire RSS sync lock
2. clone or update RSS repository
3. compute changed catalog files
4. validate and normalize JSON payloads
5. reconcile companies, feeds, and tags in Postgres
6. persist sync success or failure state

## Analysis Endpoints

### `GET /internal/admin/analysis/overview`

Returns:

- total source count
- indexed embedding count
- Qdrant collection name

### `GET /internal/admin/analysis/similar-sources`

Returns similar sources for a given `source_id`.

Parameters:

- `source_id`
- `limit`
- `worker_version` (optional override)

## Runtime Flows

### Delegated User/Job Flow

1. validate internal token
2. resolve upstream base URL and timeout
3. propagate internal token to upstream service
4. map upstream errors into local application errors
5. return validated schema payload

### RSS Sync Flow

1. validate internal token
2. serialize execution with DB-backed lock
3. update repository from Git
4. reconcile catalog state into Postgres
5. commit success or persist failure metadata
