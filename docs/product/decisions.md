# Key Decisions

## Accepted

### ADR-001: Use FastAPI as the backend framework

Status: Accepted

Reason:

- the current codebase is already built on FastAPI
- keeping FastAPI avoids unnecessary reset cost
- it aligns with the source-of-truth workflow used in the course

### ADR-002: Use PostgreSQL locally via Docker before any hosted database

Status: Accepted

Reason:

- local Postgres keeps the MVP simple and reproducible
- Docker Compose already supports the local database flow
- Supabase is deferred until the local pipeline is stable

### ADR-003: Use Docker Compose as the local orchestration layer

Status: Accepted

Reason:

- the target local environment requires backend, database, and later frontend
- Compose provides a stable local contract for development and validation

### ADR-004: Defer authentication from the MVP

Status: Accepted

Reason:

- auth is not required to validate the ETL and analytics pipeline
- adding auth now would slow delivery and expand scope

### ADR-005: Defer AI features from the MVP

Status: Accepted

Reason:

- the first milestone is a trustworthy data pipeline and analytics baseline
- AI on top of bad or unverified data would add complexity without leverage

### ADR-006: Use golden sets as the extraction quality contract

Status: Accepted

Reason:

- golden sets make extraction quality measurable
- they protect against regressions caused by PDF parsing edge cases
- they fit the contract-first approach for this project

### ADR-007: Use pdfplumber as the primary extraction engine

Status: Accepted

Reason:

- the initial dataset appears to be text-based and table-oriented
- pdfplumber is pragmatic for text PDFs and debugging
- secondary engines can be introduced later for cross-checking

### ADR-008: Persistence must be idempotent and deduplicated

Status: Accepted

Reason:

- repeated ingestion of the same PDF must not create duplicate records
- financial transaction storage must be safer than append-only ingestion
- future source expansion such as broker APIs or `yfinance` must not collide with existing transaction records

Implications:

- document records must use file hash as an idempotency key
- transaction records must use a deterministic fingerprint or natural key
- persistence must use upsert or equivalent deduplication-safe behavior
- market or reference data must be stored separately from transaction data

### ADR-009: Keep a ledger-first portfolio model

Status: Accepted

Reason:

- trustworthy analytics depend on event history, not only current holdings
- lot-level contribution analysis requires stable transaction provenance
- derived snapshots and grouped views should be reproducible from canonical records

Implications:

- canonical transactions are the system of record
- portfolio views are derived outputs
- lots must be stable and explainable from ledger events

### ADR-010: Store price history separately from the transaction ledger

Status: Accepted

Reason:

- current prices and historical quotes refresh on a different cadence than transactions
- market data should be replaceable or refreshable without mutating transaction truth
- valuation and performance metrics need explicit market data provenance

Implications:

- `price_history` and quote refresh logic live outside the core transaction ledger
- analytics must declare the pricing snapshot or timestamp used
- grouped summary valuation uses one consistent persisted snapshot per response
- lot-detail analytics remain ledger-derived unless a later approved change expands that contract
- transaction rows must not be rewritten during quote refresh

### ADR-011: Freeze accounting policy before advanced analytics expansion

Status: Accepted

Reason:

- lot-level analytics become untrustworthy if cost basis rules are implicit
- fees, dividends, FX, and corporate actions change metric interpretation materially
- early clarity prevents drift in KPI behavior and test expectations

Implications:

- cost basis method must be documented explicitly
- realized and unrealized gain rules must be documented explicitly
- fee, dividend, FX, and corporate action treatment must be documented explicitly
- advanced analytics should wait until these rules are frozen

### ADR-012: Keep broker-specific logic outside the canonical schema

Status: Accepted

Reason:

- broker-specific parsing rules are volatile and should not contaminate the shared domain model
- a broker-agnostic canonical schema makes multi-source expansion practical
- source adapters become easier to test and replace when normalization boundaries are clear

Implications:

- source adapters may emit raw or intermediate structures
- only the normalizer may emit canonical transactions
- canonical schemas and persistence models should not embed broker-only field names

### ADR-013: Keep PostgreSQL local-first with explicit security boundaries

Status: Accepted

Reason:

- the current MVP is still local-first and single-user, so local Docker PostgreSQL remains the simplest operational baseline
- local-development convenience must not blur the boundary between safe local defaults and stronger shared-environment requirements
- documenting database security posture now reduces drift when the project later adopts hosted or shared infrastructure

Implications:

- local Docker PostgreSQL remains the default development path
- local-only defaults are acceptable only for local-only usage
- local Docker setup should keep bootstrap/admin and runtime app roles separate
- shared or remote environments must use least-privilege roles, restricted client access, and TLS
- the application should not depend on superuser privileges for normal runtime behavior
- database security rules live in `docs/standards/postgres-standard.md`
- local operational steps live in `docs/guides/postgres-local-setup.md`
- database security guidance lives in `docs/guides/postgres-security-guide.md`
## Proposed

### ADR-014: Add Camelot or PyMuPDF as secondary validation engines

Status: Proposed

Reason:

- cross-engine comparison may help debug extraction mismatches
- not required for the first pass if pdfplumber is sufficient

### ADR-015: Add Pandera for DataFrame-level validation

Status: Proposed

Reason:

- Pydantic is enough for row-level contracts initially
- Pandera can be added later when tabular validation becomes more complex

### ADR-016: Treat external templates as reference patterns, not drop-in foundations

Status: Proposed

Reason:

- current roadmap scope is intentionally narrow and finance-boundary-first
- broad template adoption can inject premature AI/auth/integration complexity
- architecture drift risk is high when external templates become implicit authorities

Implications:

- external template content should be evaluated in explicit documentation notes before adoption
- only phase-scoped, minimal patterns should be imported
- every adopted pattern must preserve ledger-first truth, fail-fast behavior, and current validation gates
- drop-in template migration is out of scope unless a dedicated future change explicitly approves it

### ADR-017: Use yfinance as the first market-data provider adapter

Status: Accepted (implemented 2026-03-24; operational refresh seam + stabilization runbook hardening delivered 2026-03-25)

Reason:

- Sprint 5.2 needs a practical first provider to validate adapter boundaries and ingestion contracts
- yfinance enables a low-friction first integration while preserving current provider-agnostic schema boundaries
- provider-specific behavior can be isolated in adapter modules without changing canonical or ledger truth

Implications:

- yfinance integration remains market-data-only and must not mutate canonical/ledger/lot truth
- provenance and idempotency requirements from the current market-data boundary remain mandatory
- current provider execution posture is manual and schedule-ready through local operator command surfaces (`just market-refresh-yfinance`, `just data-sync-local`) on top of the market-data service seam
- operator refresh execution uses an explicit staged scope contract (`core` default, `100`, `200`) propagated through service and CLI boundaries for controlled onboarding
- current local-first verification posture keeps standalone `core` as required live evidence, uses representative non-core PR smoke as the default broader safeguard, treats full-scope `100` as optional manual soak, and excludes routine `200` verification
- approved live-provider recovery is bounded and explicit:
  - empty history may use ordered shorter-period fallback (`5y -> 3y -> 1y -> 6mo` default)
  - missing currency metadata may use configured default currency (`USD` default)
  - explicit invalid currency metadata and unsupported payloads still fail fast
- refresh outcomes must expose typed recovery diagnostics (`history_fallback_symbols`, `history_fallback_periods_by_symbol`, `currency_assumed_symbols`) alongside retry/failure evidence
- approved day-level temporal-key variants for operational refresh are explicit and bounded (`date`/`datetime`, `to_pydatetime()` to `date`/`datetime`, scalar `item()` conversions); unsupported temporal keys must fail fast
- operator smoke closeout must capture structured success evidence or structured blocker evidence (`status`, `stage`, `status_code`, `error`) rather than implicit/partial success
- latest closeout evidence (2026-03-26) is recorded in `docs/evidence/market-data/staged-live-smoke-2026-03-26.md` (`core` blocker `502`, `100` blocker `408`, combined `data-sync-local --refresh-scope core` completed)
- public market-data routes remain deferred; command-level operations are the active execution boundary in this slice
- legal usage notes and provider limitations must be documented explicitly
- fundamentals/financial-document payloads from yfinance are analysis-enrichment inputs, not accounting truth

### ADR-018: Quant Runtime Stack for Portfolio Estimators

Status: Accepted (2026-03-27)

Reason:

- v1 estimator delivery needs deterministic, reproducible math kernels with low operational complexity.
- the project scope is analytics/risk reporting, not full strategy backtesting or derivatives pricing.
- a narrow stack reduces hidden methodology drift and dependency risk.

Decision Matrix:

| Package | Decision | Scope | Rationale |
|---|---|---|---|
| `numpy` | Accepted | canonical estimator runtime | deterministic numeric kernels and array math foundation |
| `pandas` | Accepted | canonical estimator/runtime tabular layer | explicit time-series and contract-safe preprocessing workflows |
| `scipy` | Accepted | canonical estimator runtime (advanced methods only) | vetted statistical/optimization routines when estimator contract needs them |
| `pandas-ta` | Conditional | optional UI-facing overlays only | convenience indicators allowed, but not canonical risk truth source |
| `zipline` | Rejected (v1) | runtime estimator dependencies | backtesting framework scope exceeds current product boundary |
| `zipline-reloaded` | Rejected (v1) | runtime estimator dependencies | same scope mismatch plus added maintenance surface |
| `pyfolio` | Rejected (v1) | runtime estimator dependencies | portfolio tear-sheet tooling not required for current API contracts |
| `pyrisk` | Rejected (v1) | runtime estimator dependencies | unnecessary overlap with approved stack for baseline metrics |
| `mibian` | Rejected (v1) | runtime estimator dependencies | options-pricing focus is out of v1 scope |
| `backtrader` | Rejected (v1) | runtime estimator dependencies | strategy engine scope is out of current analytics boundary |
| `QuantLib-Python` | Rejected (v1) | runtime estimator dependencies | heavyweight derivatives toolkit not needed for v1 estimator set |

Upgrade Policy:

- quant dependency upgrades must be PR-scoped and explicit; do not batch unrelated runtime upgrades in the same PR.
- approved quant packages are pinned in `pyproject.toml` and `uv.lock`; upgrades must keep exact pins synchronized.
- each quant upgrade PR must run estimator regression fixtures and include fixture-diff review evidence before merge.

Implications:

- runtime estimator implementations are restricted to the accepted canonical stack.
- rejected packages must stay outside runtime estimator dependency closure.
- optional overlay libraries (such as `pandas-ta`) must not become canonical risk-estimator truth.

### ADR-019: Freeze v1 Estimator Methodology Contract Before Endpoint Implementation

Status: Accepted (2026-03-28)

Reason:

- endpoint implementation needs a fixed methodology contract to avoid frontend/backend interpretation drift.
- default windows, return-basis semantics, and annualization semantics are high-impact assumptions that should not be inferred during coding.

Decision:

- default estimator windows are fixed to `30`, `90`, and `252` trading-day periods for v1.
- baseline return basis is `simple` unless metric metadata explicitly declares `log`.
- annualized metrics use explicit annualization metadata with default `252` trading days unless endpoint contract explicitly overrides it.
- required methodology metadata fields for v1 responses:
  - `estimator_id`
  - `window_days`
  - `return_basis`
  - `annualization_basis.kind`
  - `annualization_basis.value`
  - `as_of_timestamp`

### ADR-020: Lock Workspace Chart Foundation to Recharts for v1

Status: Accepted (2026-03-28)

Reason:

- current delivery priority is fast, predictable workspace implementation on the existing React + Vite stack.
- chart-library churn before route-level evidence adds avoidable execution risk.

Decision:

- `Recharts` is the required v1 chart foundation for workspace routes.
- chart-library re-evaluation is allowed only with explicit route-level evidence from `/portfolio/home`, `/portfolio/analytics`, and `/portfolio/risk`.
- acceptable re-evaluation trigger evidence includes sustained chart-attributable CWV/accessibility blockers or required interactions that cannot be delivered with maintainable complexity.
- any switch requires a documented decision artifact with side-by-side evidence before implementation.

### ADR-021: Keep Transactions v1 Scope Ledger-History-Only

Status: Accepted (2026-03-28)

Reason:

- user-facing transaction history and operator refresh diagnostics serve different purposes and should not be merged in v1.
- ledger-first trust boundary is clearer when `Transactions` stays tied to persisted ledger events.

Decision:

- `Transactions` route v1 includes persisted ledger events only.
- market-refresh diagnostics are explicitly deferred to a follow-up operator-facing capability.
