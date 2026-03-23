# Roadmap

## Phase 0: Product and Delivery Foundations

- Freeze PRD v1.
- Freeze canonical extraction contract for dataset 1.
- Establish baseline validation commands and expected outcomes.
- Align repository documentation with the finance MVP.

## Phase 1: PDF ETL Foundation

- Implement secure PDF ingestion.
- Add preflight checks for extractability.
- Implement primary extraction engine for multi-page tables.
- Normalize extracted rows into canonical JSON.
- Reconcile output against the golden set.

## Phase 2: Persistence Layer

- Add document metadata persistence.
- Add normalized transaction persistence in PostgreSQL.
- Define database models and migrations.
- Preserve provenance needed for audit and reprocessing.
- Add deterministic transaction fingerprints and duplicate-safe persistence behavior.
- Keep the current local PostgreSQL baseline with separated bootstrap and app credentials, while explicitly deferring stricter runtime-role hardening blocked by current software-version constraints.

## Phase 3: Ledger and Accounting Foundation

- Derive `portfolio_transaction`, `dividend_event`, `corporate_action_event`, `lot`, and `lot_disposition` from persisted canonical records.
- Freeze `dataset_1_v1` accounting policy: FIFO sell matching, trade USD basis fields, dividend income isolation, and proportional split lot adjustments.
- Keep fee/FX adjustments explicit as unsupported in v1 rather than inferred.
- Validate deterministic finance golden cases and duplicate-safe ledger rebuild behavior for reruns and concurrency.
- Keep market data storage and analytics API work out of this phase.

## Phase 4: Portfolio Analytics API

- Implemented `GET /api/portfolio/summary` grouped analytics from persisted ledger truth.
- Implemented `GET /api/portfolio/lots/{instrument_symbol}` with deterministic symbol normalization and explicit unknown-symbol rejection.
- Implemented ledger-only KPI v1 contract (`open_*`, `realized_*`, `dividend_*`) plus `as_of_ledger_at` consistency metadata.
- Added unit and DB-backed integration coverage proving analytics reads persisted ledger state and does not trigger rebuild/PDF pipeline side effects.
- Keep market-data-dependent valuation and unrealized pricing metrics deferred to later phases.

## Phase 5: Frontend MVP

- Add React frontend container to Docker Compose.
- Build grouped table by ticker.
- Add drill-down view for lots and transactions.
- Connect frontend to analytics APIs.

## Phase 6: External Broker API Integration

- Integrate broker API for historical/reference data.
- Reconcile API-driven data with PDF-driven records where needed.
- Expand analytics scope using the additional data.
- Keep quote refresh and market data ingestion isolated from ledger mutation.

## Phase 7: Database Hardening and Deployment Readiness

- Revisit PostgreSQL and tooling version constraints that currently block stricter local and shared-environment hardening.
- Separate admin, migrator, and runtime roles more strictly once the software/runtime baseline allows it cleanly.
- Harden connection, privilege, and network posture for shared or hosted environments.
- Prepare TLS-ready PostgreSQL guidance for remote or hosted deployments.
- Re-validate extension and runtime compatibility before adopting advanced PostgreSQL features in stricter environments.

## Deferred Phases

- authentication and authorization
- AI or agentic enrichment
- Supabase migration
- production cloud deployment
