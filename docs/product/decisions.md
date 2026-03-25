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

Status: Accepted (implemented 2026-03-24)

Reason:

- Sprint 5.2 needs a practical first provider to validate adapter boundaries and ingestion contracts
- yfinance enables a low-friction first integration while preserving current provider-agnostic schema boundaries
- provider-specific behavior can be isolated in adapter modules without changing canonical or ledger truth

Implications:

- yfinance integration remains market-data-only and must not mutate canonical/ledger/lot truth
- provenance and idempotency requirements from the current market-data boundary remain mandatory
- legal usage notes and provider limitations must be documented explicitly
- fundamentals/financial-document payloads from yfinance are analysis-enrichment inputs, not accounting truth
