# Security

## Internal Service Authentication

Header used for internal authorization:

- `x-manifeed-internal-token`

Policy:

- local/test-like environments may allow missing token when not configured
- strict environments require configured token
- weak tokens are rejected in strict mode
- token comparison uses constant-time `secrets.compare_digest`

## Upstream Delegation Security

- `user_service` and `worker_service` calls reuse the same internal token model
- internal token is propagated in request headers when configured
- upstream HTTP failures are wrapped as service-level application errors

## RSS Mutation Safety

- RSS sync and RSS toggle operations are serialized with explicit lock names
- toggle operations rollback the DB session on failure
- sync failure persistence also uses guarded rollback handling

## Icon Read Safety

RSS icon file resolution rejects:

- empty paths
- absolute paths
- parent-directory traversal (`..`)
- non-SVG files
- files outside the configured RSS repository directory

## Browser-Related Middleware

- CORS is configurable through `CORS_ORIGINS`
- CSRF origin checks are applied only to unsafe `/api/*` routes
- most admin-service routes are internal `/internal/*` endpoints

## Current Security Constraints

- inter-service auth relies on a shared secret token
- environment misconfiguration can weaken route protection if local mode is
  incorrectly enabled
- no mTLS or signed service-to-service identity is built in
