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

## Proposed

### ADR-009: Add Camelot or PyMuPDF as secondary validation engines

Status: Proposed

Reason:

- cross-engine comparison may help debug extraction mismatches
- not required for the first pass if pdfplumber is sufficient

### ADR-010: Add Pandera for DataFrame-level validation

Status: Proposed

Reason:

- Pydantic is enough for row-level contracts initially
- Pandera can be added later when tabular validation becomes more complex
