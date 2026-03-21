## Why

The repository now completes the PDF ETL spine through PostgreSQL persistence, but it still stops at audit-grade canonical records instead of a ledger model that analytics can safely depend on. The next change is needed now because the roadmap, accepted decisions, and ledger guide all require a ledger-first foundation and explicit accounting policy before KPI endpoints or frontend work can be treated as trustworthy.

## What Changes

- Add a portfolio ledger foundation that derives stable dataset 1 ledger-domain records from persisted canonical PDF records instead of reparsing source files.
- Define the minimum durable ledger entities needed before analytics, including trade-ledger rows plus derived lot and lot-disposition records.
- Keep `canonical_pdf_record` as immutable ETL audit truth and derive ledger records with preserved lineage to `source_document`, `import_job`, and canonical-record fingerprints.
- Freeze a v1 accounting policy for dataset 1 covering FIFO lot matching, realized gain interpretation, unrealized gain prerequisites, dividend handling, split handling, and explicit treatment of unsupported fee or FX cases.
- Add deterministic financial golden cases that validate ledger derivation and accounting outputs independently of PDF extraction correctness.
- Keep this slice explicitly out of scope for quote ingestion, price-history storage, analytics APIs, KPI endpoints, frontend work, and multi-source reconciliation.

## Capabilities

### New Capabilities
- `portfolio-ledger`: Derive idempotent portfolio ledger and lot records from persisted canonical dataset 1 records while preserving source lineage and keeping derived analytics concerns separate.
- `portfolio-accounting`: Freeze and validate the dataset 1 accounting policy required for FIFO lot derivation, realized-gain interpretation, dividend treatment, and split handling before analytics work begins.

### Modified Capabilities
- None.

## Impact

- Adds a new ledger-focused feature slice under `app/` plus new SQLAlchemy models, derivation services, tests, and Alembic migration(s).
- Introduces the first portfolio-domain tables beyond ETL persistence, likely including ledger transactions and lot-derivation state.
- Reuses `pdf_persistence` tables as upstream audit input without changing the existing PDF ETL API contracts.
- Requires updates to product and guide documents that freeze accounting rules and ledger boundaries before later analytics work.
- Creates the contract foundation for a later analytics proposal without prematurely adding market data, valuation, or frontend scope.
