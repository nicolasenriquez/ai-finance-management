# PostgreSQL Local Setup Guide

## Purpose

This guide explains how to run PostgreSQL locally for this repository using the current project conventions while keeping local setup explicit and reasonably safe.

Use it when:

- bootstrapping the project on a new machine
- resetting local database configuration
- checking whether local setup still matches repository expectations

This guide is for local development. It does not replace stronger controls required for shared or remote environments.

## Current Local Baseline

The repository currently expects:

- PostgreSQL 18 in Docker Compose
- host port `5433`
- application port `8123`
- frontend dev port `3000`
- `DATABASE_URL` loaded from `.env`
- separate admin/bootstrap and app runtime credentials
- local workflow automation available via `just` recipes (`just db-check`, `just db-upgrade`, `just dev`)

Current examples live in:

- `.env.example`
- `docker-compose.yml`

## Local Security Posture

Local development is intentionally simpler than a shared environment, but it still has rules:

- keep PostgreSQL local-only unless there is a deliberate reason to expose it further
- do not treat default local credentials as acceptable for shared, remote, or cloud use
- keep credentials in `.env`, not in committed code or shell history where avoidable
- do not reuse local development credentials in other environments

## Recommended Local Setup

### 1. Create local environment configuration

Start from:

```bash
cp .env.example .env
```

Minimum values to review:

- `ENVIRONMENT=development`
- `POSTGRES_ADMIN_PASSWORD`
- `POSTGRES_APP_USER`
- `POSTGRES_APP_PASSWORD`
- `POSTGRES_APP_DB`
- `DATABASE_URL=postgresql+asyncpg://ai_finance_app:...@localhost:5433/ai_finance_management`

For local setup, replace the placeholder passwords before first boot.

The runtime split is now:

- admin/bootstrap role: `postgres`
- runtime application role: `ai_finance_app` by default

The repository defaults remain local-only placeholders, not shared-environment credentials.

### 2. Start PostgreSQL

Use:

```bash
docker-compose up -d db
```

This should start the local PostgreSQL container and bind it to `localhost:5433`.

On first initialization, Docker also runs the repository init script that:

- creates the application login role
- creates the application database
- grants the runtime role access to schema `public`

### 3. Apply migrations

Use:

```bash
uv run alembic upgrade head
```

This confirms:

- the connection string works
- the database is reachable
- the current schema can be applied cleanly

### 4. Start the application

Use:

```bash
uv run uvicorn app.main:app --reload --port 8123
```

### 5. Verify health endpoints

Use:

```bash
curl -s http://localhost:8123/health
curl -s http://localhost:8123/health/db
curl -s http://localhost:8123/health/ready
```

These checks confirm that the app and database are aligned with the local baseline.

## Secure-Enough Local Defaults

For this repository, secure-enough local development means:

- PostgreSQL is used only from the local machine or local Docker network
- no remote clients are intentionally allowed
- credentials are scoped to the local environment
- the app does not depend on superuser behavior for normal runtime flows

If any of those assumptions stop being true, move to the stronger posture documented in `docs/guides/postgres-security-guide.md`.

## Stronger Local Option

If you want a more disciplined local setup even before moving to shared infrastructure:

- replace the default password with a unique local password
- keep the dedicated application database role
- keep the database bound only to local interfaces

Example direction:

```text
admin/setup role: postgres
runtime role: ai_finance_app
database: ai_finance_management
```

This is not required yet for the current local baseline, but it is a better bridge to future hosted environments.

## What To Check If Local Setup Fails

### Port collision

If `5433` is already in use:

- stop the conflicting service
- or change the host-side port in `docker-compose.yml`
- then update `DATABASE_URL` in `.env`

### Wrong connection string

Check:

- host
- port
- database name
- username
- password
- async driver prefix `postgresql+asyncpg://`

### Migrations fail after schema drift

Check whether:

- the local volume contains stale data from an older schema state
- the migration history table is out of sync
- recent local manual database edits created drift

Resolve carefully. Do not normalize drift by making undocumented manual changes.

### Credential changes do not take effect

The init script only applies when PostgreSQL initializes a fresh data directory.

If you changed bootstrap or application credentials after the volume already existed, you may need to recreate the local database volume intentionally.

For a disposable local reset:

```bash
docker-compose down -v
docker-compose up -d db
uv run alembic upgrade head
```

Use that only when you are willing to discard local database state.

## Local Setup Rules

- use `.env.example` as the baseline template
- prefer Docker Compose for reproducible local setup
- keep migration application explicit
- keep database exposure local-only by default
- document any stronger or nonstandard local setup in repo docs if it becomes the new baseline

## References

- `docs/guides/postgres-security-guide.md`
- `docs/standards/postgres-standard.md`
- `docker/db/init/01-create-app-role.sh`
- `docker-compose.yml`
- `.env.example`
