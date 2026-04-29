# Development and Testing

## Local Setup

Install dependencies:

```bash
python3 -m pip install -r requirements.txt
```

Minimum local environment:

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

Run the service:

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

## Docker

Build:

```bash
docker build -t manifeed-admin-service -f admin_service/Dockerfile admin_service
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

## Tests

Run all tests:

```bash
pytest -q
```

Current automated coverage is minimal and mainly validates source compilation.

Recommended next tests:

- internal token behavior across environment modes
- route-level tests for delegated user/job endpoints
- health endpoint tests for Postgres, Redis, and Qdrant failure modes
- DB integration tests for RSS sync and RSS toggle operations
- upstream contract tests for `user_service` and `worker_service`
