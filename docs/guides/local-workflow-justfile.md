# Local Workflow with Justfile

## Purpose

This guide defines the recommended local developer workflow using repository `just` recipes.

Use it to:

- bootstrap dependencies
- run the local app stack
- run backend/frontend validation gates before push or PR

## Install Just

macOS (Homebrew):

```bash
brew install just
```

Verify:

```bash
just --version
```

## Bootstrap

```bash
cp .env.example .env
just install
```

Define isolated runtime and test database URLs in `.env`:

```bash
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management
TEST_DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management_test
```

Guardrail notes:

- `just dev` now runs `db-runtime-guard` and fails fast if runtime DB resolves to a test database target.
- `just test` and `just test-integration` now require `TEST_DATABASE_URL` and reject equal runtime/test URLs.

If PostgreSQL is not already running from Postgres.app, start Docker DB:

```bash
docker-compose up -d db
```

## Run App Locally

Run backend + frontend together:

```bash
just dev
```

Endpoints:

- backend: `http://localhost:8123`
- frontend: `http://localhost:3000`

Run components individually:

```bash
just backend
just frontend
```

## Validation Gates

Backend-focused gates:

```bash
just lint
just type
just security
just secret-scan-pr
just test
just test-integration
just backend-ci
```

Notes:

- `just secret-scan-pr` runs `gitleaks` against the PR-equivalent history range (`merge-base(origin/main, HEAD)..HEAD`) using `.gitleaks.toml`.
- if `origin/main` is stale or missing locally, run `git fetch origin main` first.

Database-target behavior:

- `just test` runs pytest with `DATABASE_URL` bound to `TEST_DATABASE_URL` for that command context.
- `just test-integration` runs `alembic upgrade head` against `TEST_DATABASE_URL` first, then runs integration tests with test DB context.

Frontend-focused gates:

```bash
just frontend-lint
just frontend-type
just frontend-test
just frontend-build
just frontend-ci
```

Full local pre-CI gate:

```bash
just ci
```

## Local Data-Sync Operations

Prerequisites:

- `DATABASE_URL` is configured
- migrations are at head (`just db-upgrade`)
- for `just` recipes in this section, `db-check` and `db-upgrade` are already enforced before command execution

Run `dataset_1` bootstrap only (`ingest -> persist -> rebuild`):

```bash
just data-bootstrap-dataset1
```

Run supported-universe `yfinance` refresh only:

```bash
just market-refresh-yfinance
```

Run combined fail-fast sync (`bootstrap -> refresh`):

```bash
just data-sync-local
```

Build or refresh the versioned market-data symbol universe library (required portfolio + starter 100/200):

```bash
just market-symbol-universe-build
```

Optional overrides:

```bash
just data-bootstrap-dataset1 app/golden_sets/dataset_1/202602_stocks.pdf
just market-refresh-yfinance 2026-03-25T00:00:00Z
just data-sync-local app/golden_sets/dataset_1/202602_stocks.pdf 2026-03-25T00:00:00Z
just market-refresh-yfinance 2026-03-25T00:00:00Z core
just market-refresh-yfinance 2026-03-25T00:00:00Z 100
just data-sync-local app/golden_sets/dataset_1/202602_stocks.pdf 2026-03-25T00:00:00Z core
just market-symbol-universe-build app/golden_sets/dataset_1/202602_stocks.json app/market_data/symbol_universe.v1.json
```

Smoke evidence contract for `market-refresh-yfinance` and `data-sync-local`:

- successful runs should capture typed evidence (`refresh_scope_mode`, `source_provider`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`)
- blocked runs should capture structured fail-fast payload (`status`, `stage`, `status_code`, `error`)
- blocked outcomes are first-class operational evidence and must not be reported as partial success
- if a staged scope is intentionally deferred from the active smoke cycle, record the deferral explicitly in evidence/readiness notes

## Git Hooks

Install hooks:

```bash
just precommit-install
```

Run hooks manually:

```bash
just precommit-run
```
