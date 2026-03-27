# Validation Baseline

## Purpose

This project uses validation as a delivery gate, not as a best-effort check.

The first baseline validates the repository itself before feature work. Later baselines validate extraction correctness against golden sets.

Current implementation status:

- dataset 1 extraction is implemented
- dataset 1 canonical normalization is implemented
- dataset 1 verification reporting is implemented
- PostgreSQL persistence and duplicate-safe reprocessing are implemented
- portfolio-ledger foundation and dataset 1 v1 accounting policy are implemented
- portfolio analytics API (`/api/portfolio/summary`, `/api/portfolio/lots/{instrument_symbol}`) is implemented with ledger-only KPI v1 scope
- market-data ingestion boundary is implemented with idempotent snapshot writes and explicit non-mutation guarantees for canonical/ledger truth
- first external market-data provider adapter (`yfinance`) is implemented with deterministic day-level close normalization and provider-backed ingest routed through the existing market-data boundary
- local data-sync operations are implemented for `dataset_1` bootstrap and `yfinance` refresh (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`)
- market-data operational smoke contract is stabilized: approved live temporal-key variants are bounded and blocked runs are captured as structured evidence instead of partial success
- live-provider stabilization contract is implemented: bounded empty-history fallback ladder, bounded default-currency assumption for missing metadata, and typed refresh recovery diagnostics (`history_fallback_*`, `currency_assumed_*`)
- latest staged smoke evidence is recorded in `docs/evidence/market-data/staged-live-smoke-2026-03-26.md` (`core` blocker `502`, `100` blocker `408`, combined `data-sync-local` with `core` scope completed)
- market-refresh verification posture is rebalanced for local-first execution: `core` remains the required live gate, representative non-core PR smoke is the default broader-than-core safeguard, full `100` refresh coverage is optional manual soak, and `200` is excluded from routine verification

## Repository Baseline

Expected commands:

```bash
export OPENSPEC_TELEMETRY=0
just lint
just type
just security
just test
just frontend-ci
just ci
just test-integration
just data-bootstrap-dataset1
just market-refresh-yfinance
just data-sync-local
openspec validate --specs --all
```

Command intent:

- `just ci`: local pre-CI gate (backend + frontend)
- `just test`: non-integration/unit-focused test run using isolated `TEST_DATABASE_URL`
- `just test-integration`: integration-only tests using isolated `TEST_DATABASE_URL` with test-db migration preflight (`test-db-upgrade`)

Database URL isolation prerequisites:

- `DATABASE_URL` and `TEST_DATABASE_URL` must both be configured
- `DATABASE_URL` and `TEST_DATABASE_URL` must not resolve to the same value
- runtime workflows must not target `_test` database names
- if `TEST_DATABASE_URL` uses non-admin app credentials, set `TEST_DATABASE_ADMIN_URL` so `test-db-upgrade` can bootstrap DB creation/schema privileges deterministically

Expected service checks:

```bash
curl -s http://localhost:8123/health
curl -s http://localhost:8123/health/db
curl -s http://localhost:8123/health/ready
```

Expected infrastructure checks:

```bash
# Option A: Docker Compose
docker-compose up -d db
docker-compose up -d --build
docker-compose ps

# Option B: local PostgreSQL app/service
uv run alembic upgrade head
```

Expected test DB setup check:

```bash
just test-db-check
just test-db-upgrade
```

## Extraction Baseline

For each golden set dataset:

- run extraction from stored upload
- run canonical normalization from stored upload
- run verification report generation from stored upload
- run persistence from stored upload
- compare verification result and mismatch evidence against expected contract
- fail the build if required fields mismatch

## Validation Levels

### Level 1: Static Analysis, Security, and Type Safety

- Ruff
- Black
- Bandit
- MyPy
- Pyright
- ty

### Level 2: Unit Tests

- pure normalizer tests
- parser tests
- schema validation tests
- non-integration backend tests (`just test`)

### Level 3: Integration Tests

- extraction against dataset 1
- persistence flow with PostgreSQL
- API flow for upload/extract/validate
- duplicate-ingestion flow for the same PDF and same transaction set
- portfolio-ledger rebuild duplicate-safety for rerun and concurrent execution
- portfolio analytics summary/lot-detail routes against persisted ledger rows
- analytics read-only guardrails (no implicit rebuild/PDF pipeline side effects during analytics requests)
- market-data snapshot ingest duplicate-safety and explicit in-request duplicate rejection
- market-data refresh non-mutation guarantees for canonical, ledger, lot, dividend, and corporate-action truth
- migration schema contract checks for `market_data_snapshot` / `price_history` boundary constraints
- provider-backed ingest idempotency/non-mutation coverage using mocked adapter responses (no live network dependency in CI)
- backend integration marker suite (`just test-integration`)

### Level 4: Manual Verification

- inspect extraction report for dataset 1
- inspect stored rows
- inspect portfolio analytics response shape
- run one required supported-universe `yfinance` refresh smoke invocation for `core` and record explicit success/blocker evidence
- run one representative broader-than-core smoke lane (`core` plus deterministic non-core sample) and record explicit success/blocker evidence
- run full-scope `100` refresh only when deliberate manual soak/tuning evidence is needed
- run one combined local sync smoke invocation and record:
  - success evidence fields from typed refresh/sync output (`refresh_scope_mode`, `source_provider`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, insert/update counters)
  - recovery evidence fields from typed refresh output (`retry_attempted_symbols`, `failed_symbols`, `history_fallback_symbols`, `history_fallback_periods_by_symbol`, `currency_assumed_symbols`)
  - blocker evidence fields from fail-fast payload (`status`, `stage`, `status_code`, `error`)
- avoid routine `200` smoke in the current local-first workflow and track any future `200` validation as explicit follow-up scope

## Reporting Rule

Every major implementation phase should produce:

- validation status
- failures with concrete evidence
- next corrective action

For persistence phases, validation must also confirm:

- rerunning the same source does not create duplicate document records
- rerunning the same source does not create duplicate transaction rows
- rerunning the same canonical source does not create duplicate portfolio-ledger, lot, or lot-disposition rows
- rerunning the same source creates a new successful `import_job` row only when the full request commits
- same-hash uploads from a different `storage_key` reuse the original `source_document` row and keep first-seen metadata
- persistence replay remains anchored to stored PDFs plus ingestion metadata manifests
- v1 scope remains single-source (dataset 1 PDF); multi-source reconciliation is intentionally deferred
- rerunning the same market-data snapshot uses deterministic insert-or-update behavior instead of creating ambiguous duplicate rows
- market-data ingestion rejects payload-level duplicate symbol/time keys before DB mutation
- market-data refresh path does not create, update, or delete canonical, ledger, lot, lot-disposition, dividend, or corporate-action truth rows
- market-data provider normalization accepts only the approved day-level temporal variants and rejects unsupported variants explicitly
- provider-adapter tests prove fail-fast behavior for unsupported config semantics and incomplete requested-symbol coverage
- provider-adapter and refresh tests prove explicit blocker evidence when configured history fallback is exhausted for required symbols
- when manual provider smoke checks fail, capture the explicit adapter/service rejection with `status`, `stage`, `status_code`, and `error` and track it as an operational blocker before change closeout
