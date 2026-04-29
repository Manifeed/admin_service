# Configuration

## Core Runtime

- `APP_ENV`
- `ENVIRONMENT`
- `NODE_ENV`
- `CONTENT_DATABASE_URL`
- `IDENTITY_DATABASE_URL`
- `DATABASE_URL`
- `REQUIRE_EXPLICIT_DATABASE_URLS`
- `INTERNAL_SERVICE_TOKEN`
- `REQUIRE_INTERNAL_SERVICE_TOKEN`

Notes:

- `CONTENT_DATABASE_URL` falls back to `DATABASE_URL`
- in production-like environments, DB URLs must be explicit unless
  `REQUIRE_EXPLICIT_DATABASE_URLS` disables that behavior

## Upstream Services

- `USER_SERVICE_URL`
	- base URL for delegated admin user requests

- `USER_SERVICE_TIMEOUT_SECONDS`
	- default: `5.0`

- `WORKER_SERVICE_URL`
	- base URL for delegated job and worker requests

- `WORKER_SERVICE_TIMEOUT_SECONDS`
	- default: `10.0`

## Health / Dependency Variables

- `REDIS_URL`
	- default: `redis://redis:6379/0`

- `REDIS_SOCKET_TIMEOUT_SECONDS`
	- default: `0.2`

- `QDRANT_URL`
	- default: `http://qdrant:6333`

- `QDRANT_COLLECTION_NAME`
	- default: `article_embeddings`

- `QDRANT_API_KEY`
	- optional

- `HEALTH_INCLUDE_DETAILS`
	- when unset, detailed responses are reduced in production-like environments

## RSS Repository Variables

- `RSS_FEEDS_REPOSITORY_URL`
	- default: `https://github.com/Manifeed/rss_feed`

- `RSS_FEEDS_REPOSITORY_BRANCH`
	- default: `main`

- `RSS_FEEDS_REPOSITORY_PATH`
	- default: `var/rss_feeds`

## Analysis Variables

- `SOURCE_EMBEDDING_WORKER_VERSION`
	- default: `e5-large-v1`

- `SOURCE_EMBEDDING_DIMENSIONS`
	- optional integer override

## HTTP / Browser-Related Variables

- `CORS_ORIGINS`
- `CSRF_TRUSTED_ORIGINS`
- `CSRF_TRUST_SELF_ORIGIN`

## Database Pool Variables

- `DB_POOL_SIZE` (default: `20`)
- `DB_MAX_OVERFLOW` (default: `40`)
- `DB_POOL_TIMEOUT_SECONDS` (default: `30`)
- `DB_POOL_RECYCLE_SECONDS` (default: `1800`)
