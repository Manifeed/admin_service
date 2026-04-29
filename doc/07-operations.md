# Operations

## Production Recommendations

- set `APP_ENV=production` (or explicit staging value)
- configure strong `INTERNAL_SERVICE_TOKEN` (minimum 32 characters)
- set explicit `CONTENT_DATABASE_URL` and `IDENTITY_DATABASE_URL`
- configure `USER_SERVICE_URL` and `WORKER_SERVICE_URL` explicitly
- monitor health degradation across Postgres, Redis, and Qdrant
- monitor RSS sync failures and lock contention

## Known Constraints

- inter-service auth still relies on a shared secret token
- delegated upstream contracts are locally duplicated and can drift
- Redis command sequences are not fully atomic where TTL behavior matters
- `rss_public_router` exists in code but is not currently registered by `main.py`
- Docker runtime still runs from a relatively broad base image configuration

## Suggested Monitoring

- dependency health status changes
- upstream request latency and failure rate
- RSS sync success/failure counts
- RSS lock contention events
- DB pool saturation
- Qdrant query errors and latency

## Documentation Maintenance

Update docs in this folder whenever behavior changes in:

- `main.py`
- `database.py`
- `app/internal/*`
- `app/health/*`
- `app/routers/*`
- `app/services/*`
- `app/rss/*`
- `app/analytics/*`
- `app/clients/networking/*`
