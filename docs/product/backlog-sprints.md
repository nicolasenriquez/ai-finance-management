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

Definition of Done:

- extracted dataset 1 can be persisted in PostgreSQL
- migrations run cleanly on local Docker Postgres
- stored rows preserve provenance needed for audit and reprocessing
- reprocessing the same PDF does not create duplicate document records
- reprocessing the same transaction set does not create duplicate transaction rows
- duplicate-safe persistence behavior is covered by tests

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

### Item 4.3: Add React frontend container and grouped-table MVP

- add frontend service to Docker Compose
- implement grouped table by ticker
- implement drill-down into individual transactions or lots

Definition of Done:

- `db`, `backend`, and `frontend` run together via Docker Compose
- grouped ticker view is visible in the browser
- drill-down view displays per-purchase details and KPIs

## Sprint 5: External Broker API and Market Data

### Item 5.1: Add market data ingestion boundary

- ingest current quotes and historical prices separately from transactions
- persist market data with explicit source and timestamp
- keep quote refresh idempotent

Definition of Done:

- quote refresh does not mutate canonical transaction rows
- analytics can declare which price snapshot they used

### Item 5.2: Add broker API integration

- define source adapter boundary for broker API ingestion
- normalize API-driven transaction or reference data into canonical forms where appropriate
- preserve source provenance and deduplication rules

Definition of Done:

- API integration does not bypass canonical normalization
- PDF and API sources can coexist without record-type confusion

## Exit Criteria for MVP

- dataset 1 is extracted deterministically
- verification report is generated and trusted
- normalized records are stored in PostgreSQL
- grouped and lot-level analytics are visible in the frontend
- repository validation baseline remains green
- accounting rules are frozen and reflected in tests

## Explicitly Deferred Beyond Sprint 5

- authentication
- AI features and agent workflows
- Supabase migration
- cloud deployment
