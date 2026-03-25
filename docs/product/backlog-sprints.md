# Backlog by Sprint

## Sprint 0: Foundations and Contracts

### Item 0.1: Freeze product and delivery documents

- Review and approve `docs/product/prd.md`
- Review and approve `docs/product/decisions.md`
- Review and approve `docs/product/roadmap.md`

Definition of Done:

- product scope is frozen for MVP
- out-of-scope items are explicit
- FastAPI, PostgreSQL, Docker Compose, no-auth, no-AI decisions are accepted

### Item 0.2: Freeze golden set contract for dataset 1

- confirm `app/golden_sets/dataset_1/202602_stocks.pdf`
- confirm `app/golden_sets/dataset_1/202602_stocks.json`
- document any known limitations of the dataset

Definition of Done:

- dataset 1 is treated as the extraction source of truth
- change management rule is documented and accepted

### Item 0.3: Establish repository validation baseline

- run unit tests
- run integration tests
- run MyPy
- run Pyright
- run ty
- run Ruff
- run Black (check mode)
- run Bandit (app security scan)
- validate health endpoints and local Docker flow

Definition of Done:

- validation commands are documented and reproducible
- baseline result is recorded with pass/fail status
- blockers are listed explicitly if anything is red

## Sprint 1: PDF ETL Spine

### Item 1.1: Implement secure PDF ingestion

- add upload boundary
- enforce MIME, size, and page-count constraints
- generate document ID and SHA-256 hash
- persist original file in a safe storage path

Definition of Done:

- PDF upload works through a FastAPI endpoint or service boundary
- invalid files are rejected with explicit errors
- file hash and metadata are captured deterministically

### Item 1.2: Implement preflight analysis

- detect encrypted PDFs
- detect low-text or likely scanned PDFs
- fail clearly when OCR would be required but is not enabled

Definition of Done:

- preflight returns explicit extractability status
- non-supported PDFs fail without ambiguous behavior

### Item 1.3: Implement extraction with `pdfplumber`

- iterate multi-page tables
- remove repeated headers
- filter footer artifacts
- preserve source page provenance

Definition of Done:

- dataset 1 produces row-wise raw extraction output
- repeated headers are not duplicated as rows
- source page is present for every extracted row

### Item 1.4: Implement canonical mapping and normalization

- map source headers to canonical fields
- normalize dates
- normalize decimal-comma numbers
- normalize currency values
- convert blank values to `None`

Definition of Done:

- extracted rows contain both raw and normalized fields
- normalization is covered by unit tests
- no inferred values are introduced

## Sprint 2: Reconciliation and Persistence

### Item 2.1: Implement schema validation

- add row-level Pydantic models
- enforce invariants such as `aporte XOR rescate`
- reject malformed records before persistence

Definition of Done:

- invalid rows fail validation with actionable messages
- canonical models are the single contract for extracted rows

### Item 2.2: Implement reconciliation and verification report

- compare extraction output against expected raw values
- emit mismatch evidence by page, row, and column
- generate `verification_report.json`

Definition of Done:

- dataset 1 can produce a machine-readable verification report
- mismatches include enough evidence to debug quickly
- report format is deterministic

### Item 2.3: Persist document metadata and normalized rows

- create database models
- add Alembic migrations
- store document metadata, provenance, and normalized transactions
- implement document-level deduplication using file hash
- implement transaction-level deduplication using deterministic fingerprint or natural key
- use persistence behavior that only adds missing records
- keep the local PostgreSQL baseline on separated bootstrap and app credentials
- explicitly defer stricter runtime-role hardening if blocked by current software-version constraints

Definition of Done:

- extracted dataset 1 can be persisted in PostgreSQL
- migrations run cleanly on local Docker Postgres
- stored rows preserve provenance needed for audit and reprocessing
- reprocessing the same PDF does not create duplicate document records
- reprocessing the same transaction set does not create duplicate transaction rows
- duplicate-safe persistence behavior is covered by tests
- the local database baseline documents any remaining security compromises caused by current software-version constraints

## Sprint 3: Ledger and Accounting Foundation

### Item 3.1: Formalize ledger entities for portfolio analytics

- define canonical ledger entities required for lot tracking
- distinguish transaction ledger records from derived position snapshots
- define market data entities separately from ledger tables

Definition of Done:

- entity boundaries are documented and reflected in implementation planning
- transaction records remain the system of record
- price history is not stored as transaction data

### Item 3.2: Freeze accounting policy

- choose and document cost basis method
- define realized and unrealized gain rules
- define fee handling
- define dividend handling
- define FX handling
- define split and corporate action handling

Definition of Done:

- accounting rules are documented explicitly
- analytics implementation does not depend on hidden assumptions
- financial test scenarios can be derived from the documented policy

### Item 3.3: Add financial calculation golden cases

- define test cases for lot contribution
- define test cases for realized and unrealized gain
- define test cases for fees and dividends
- define test cases for FX-sensitive calculations if applicable

Definition of Done:

- financial calculation cases are deterministic
- tests can prove analytics correctness beyond extraction correctness

## Sprint 4: Analytics API and Frontend MVP

### Item 4.1: Implement analytics service layer

- aggregate by ticker
- expose lot-level transaction detail
- define first KPI set
- expose lot-level contribution breakdown

Definition of Done:

- KPI formulas are frozen and documented
- analytics logic is covered by unit tests
- grouped and detail responses are stable and typed
- analytics are computed from deduplicated transaction storage, not duplicate raw rows
- lot-level contribution can be explained from ledger plus price history

### Item 4.2: Expose analytics endpoints

- add FastAPI routes for grouped portfolio data
- add routes for individual transaction or lot views

Definition of Done:

- analytics endpoints return typed responses
- integration tests cover at least one end-to-end analytics flow

### Item 4.3: Lock frontend foundation before UI feature delivery

- freeze the frontend design-system baseline
- define semantic tokens for typography, color, spacing, and motion
- define responsive behavior for summary and lot-detail views
- map backend analytics responses to UI states, formatting, and copy
- define error-state handling for `404`, `422`, and `500`
- formalize decimal-safe frontend numeric handling for finance fields

Definition of Done:

- frontend implementation can rely on one documented design system and API-to-UI contract
- unsupported market-value and FX-sensitive behavior is explicitly excluded from the MVP
- loading, empty, not-found, validation-error, and server-error states are defined before screen implementation
- frontend quality gates are documented for accessibility, performance, and evidence capture

### Item 4.4: Deliver summary and lot-detail frontend MVP

- add frontend service to Docker Compose
- implement grouped portfolio summary by instrument
- implement drill-down into lot detail from summary interactions
- surface `as_of_ledger_at` and ledger-only scope context in the UI
- keep row interaction keyboard accessible and deterministic

Definition of Done:

- `db`, `backend`, and `frontend` run together via Docker Compose
- grouped summary view is visible in the browser and backed by `GET /api/portfolio/summary`
- lot-detail view is visible in the browser and backed by `GET /api/portfolio/lots/{instrument_symbol}`
- core formatting, copy, and interaction behavior matches the documented frontend contract

### Item 4.5: Harden frontend UX, accessibility, and performance

- verify keyboard navigation, focus visibility, and target-size behavior
- verify contrast and reduced-motion behavior
- measure Core Web Vitals on key screens
- capture review artifacts for responsive layouts and error states
- close any UX ambiguity that hides unsupported or missing data

Definition of Done:

- WCAG 2.2 AA baseline expectations are met for the MVP screens
- Core Web Vitals targets are measured and acceptable for the MVP screens
- evidence artifacts exist for summary, lot detail, not-found, and error states
- frontend release readiness is based on documented quality gates, not visual inspection alone

## Sprint 5: External Broker API and Market Data

### Item 5.1: Add market data ingestion boundary

Status: Implemented (2026-03-24)

- ingest current quotes and historical prices separately from transactions
- persist market data with explicit source and timestamp
- keep quote refresh idempotent
- enforce deterministic duplicate rejection for same symbol/time keys in one request payload
- preserve canonical symbol forms from `dataset_1` ledger truth (including dotted tickers such as `BRK.B`)
- keep the first slice internal-only (no market-value API expansion in this item)

Definition of Done:

- quote refresh does not mutate canonical transaction rows
- analytics can declare which price snapshot they used
- integration tests prove refresh path non-mutation for canonical, ledger, lot, dividend, and corporate-action truth
- unit tests prove fail-fast validation for provenance, unsupported symbols, and duplicate symbol/time payload rows

### Item 5.2: Add broker/provider API integration

Status: In progress (first-slice yfinance adapter + operational stabilization implemented 2026-03-25; live-provider smoke remains blocker-driven)

Delivered in first slice:

- define and implement provider adapter boundary under `app/market_data/providers`
- normalize provider rows into the existing market-data write contract and ingest through `ingest_market_data_snapshot`
- preserve explicit provenance and deterministic snapshot identity for provider-backed writes
- enforce fail-fast provider behavior for unsafe/incomplete symbol coverage and unsupported config semantics
- validate provider-backed idempotency and ledger/canonical non-mutation with deterministic tests
- add one explicit full-refresh orchestration seam (`refresh_yfinance_supported_universe`) anchored to the supported symbol universe
- add staged refresh-scope modes on the orchestration seam (`core` default, `100`, `200`) with explicit selector validation
- harden close-payload normalization for approved runtime series/tabular shapes with explicit unsupported-shape rejection
- add operator command workflows for local/manual execution:
  - `data-bootstrap-dataset1` (ingest -> persist -> rebuild)
  - `market-refresh-yfinance` (supported-universe refresh)
  - `data-sync-local` (strict fail-fast sequence: bootstrap then refresh)
- propagate refresh-scope selectors through command surfaces for staged onboarding (`--refresh-scope core|100|200`)
- formalize schedule-ready invocation posture on top of the existing command surfaces (no scheduler/queue infrastructure in this slice)
- freeze operator smoke evidence contract:
  - success evidence from typed refresh/sync results (`source_provider`, `requested_symbols`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, insert/update counters)
  - blocked evidence from structured fail-fast payload (`status`, `stage`, `status_code`, `error`)
- harden approved day-level temporal key variants required for current live operations (`date`/`datetime`, `to_pydatetime()` to `date`/`datetime`, scalar `item()` conversions) while preserving explicit fail-fast rejection for unsupported variants

Remaining for full item:

- resolve environment-dependent live-provider blocker patterns surfaced by manual smoke runs (for example missing provider currency metadata)
- resolve staged live-provider blockers across onboarding sequence (`core -> 100 -> 200`) before treating wider scopes as operationally ready
- evaluate broker-authenticated and multi-provider expansion only after the current operational workflow is stable
- keep transaction-import/API-source reconciliation explicitly out of this market-data-only slice unless a dedicated change expands scope

Definition of Done:

- provider integration does not bypass market-data or canonical normalization boundaries
- PDF and API/provider sources can coexist without record-type confusion
- automated provider-adapter tests remain deterministic (no live-provider dependency in CI)

## Sprint 6: Database Hardening and Deployment Readiness

### Item 6.1: Revisit PostgreSQL hardening blocked by current version constraints

- review PostgreSQL, Docker, and tooling-version constraints that currently limit stricter hardening
- decide whether admin, migrator, and runtime roles can be separated more strictly
- review privilege boundaries required for migrations versus runtime behavior
- document the accepted target posture for shared or hosted environments

Definition of Done:

- current blockers are documented explicitly
- target role separation is defined
- remaining local-security compromises are either removed or intentionally accepted

### Item 6.2: Harden network and connection posture for shared environments

- define remote/shared-environment expectations for TLS
- define `pg_hba.conf` and network exposure policy
- define credential rotation and privilege review expectations
- confirm runtime posture before any hosted PostgreSQL adoption

Definition of Done:

- shared-environment database access rules are documented explicitly
- TLS and access-control expectations are clear
- hosted or remote PostgreSQL work has a defined security baseline

## Exit Criteria for MVP

- dataset 1 is extracted deterministically
- verification report is generated and trusted
- normalized records are stored in PostgreSQL
- grouped and lot-level analytics are visible in the frontend
- frontend MVP meets documented accessibility and performance gates
- repository validation baseline remains green
- accounting rules are frozen and reflected in tests

## Explicitly Deferred Beyond Sprint 5

- authentication
- AI features and agent workflows
- Supabase migration
- cloud deployment
