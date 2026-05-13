# Overview

## Service Purpose

`admin_service` is the internal administration backend for Manifeed.
It provides admin-facing backend endpoints for operational dashboards, RSS
catalog management, and delegated workflows that are owned by other internal
services.

This service is designed for trusted internal consumers and should not be
exposed directly to browsers or public clients.

## Responsibilities

- Expose service liveness and detailed dependency health
- Aggregate admin statistics across content, identity, and worker state
- Read and mutate RSS catalog state
- Synchronize RSS catalog data from a Git repository
- Proxy admin user reads and updates to `user_service`
- Proxy job and automation operations to `worker_service`

## Technical Stack

- FastAPI
- SQLAlchemy + psycopg + PostgreSQL
- HTTPX for internal service delegation
- Redis for health visibility and reusable networking utilities
- Qdrant for dependency health visibility
- Git-backed RSS repository synchronization
