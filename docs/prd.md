# Product Requirements Document

## Executive Summary

AI Finance Management is a personal finance analytics application for consolidating investment activity across fragmented sources into a single trustworthy view.

The initial MVP focuses on a contract-first data pipeline:

- ingest broker PDFs without official APIs
- extract multi-page transaction tables into canonical JSON
- validate the extracted output against golden sets
- persist normalized records in PostgreSQL
- expose analytics and KPIs for a React frontend

This MVP does **not** include authentication or AI features.

## Problem

Current broker and finance apps are insufficient for the author's workflow because:

- portfolio data is fragmented across multiple applications
- built-in KPIs are limited and hard to customize
- there is no easy way to audit extraction quality when one source is only available as PDF
- existing tools do not expose the grouped and lot-level analytics needed for practical decision-making

The project also serves a second goal: building senior-level software and data-engineering capability through a real system that includes ingestion, normalization, persistence, validation, and analytics.

## Goals

- Build a reliable PDF-to-JSON extraction workflow for broker statements.
- Create a canonical transaction model that can support both PDF and API-based sources.
- Persist normalized portfolio data in PostgreSQL.
- Compute auditable portfolio KPIs from source transactions.
- Visualize grouped and transaction-level portfolio performance in a frontend.
- Use golden-set-driven validation so extraction quality is measurable and reproducible.

## Non-Goals

- No authentication or authorization in MVP.
- No GenAI or agentic features in MVP.
- No production cloud deployment in MVP.
- No advanced UI/UX polish in MVP.
- No multi-user support in MVP.

## Target User

Primary user:

- the repository owner, acting as a power user who wants deeper personal investment analytics than broker dashboards provide

Secondary user profile for design purposes:

- technically capable retail investor who can run local services and wants full auditability of imported transactions

## MVP Scope

### In Scope

- Upload a PDF statement and store the original file safely.
- Preflight the PDF to determine whether extraction can proceed without OCR.
- Extract one or more transaction tables spanning multiple pages.
- Normalize rows into canonical JSON with raw and typed fields.
- Validate extracted rows against a golden set and emit a verification report.
- Persist document metadata and normalized transaction rows in PostgreSQL.
- Ingest broker market/reference data from an external API for historical enrichment.
- Expose portfolio and KPI data through FastAPI endpoints.
- Build a basic React frontend with grouped tables by ticker and transaction drill-down.

### Out of Scope

- OCR-heavy workflows as a first-class supported mode
- AI-based enrichment or anomaly explanation
- account linking across multiple institutions
- auth, roles, or permissions
- mobile-first UX

## Source Systems

### Source 1: Broker PDF Statements

The first source of truth is a broker PDF that contains multi-page transaction tables.

Contract-first dataset:

- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

### Source 2: Broker API

An external broker API will be used to pull historical market or broker-side data, initially targeting at least five years of data where feasible.

## Data Contract

The extraction pipeline must produce deterministic JSON with:

- document metadata
- canonical table definitions
- row-wise records
- raw cell text as source of truth
- normalized typed values
- provenance such as page number and row identity

Validation must produce:

- row-wise and field-wise reconciliation output
- mismatch counts
- actionable evidence for debugging

Blank cells must remain `null`. The system must not hallucinate or infer missing values.

## Functional Requirements

### PDF Ingestion

- Accept PDF uploads through FastAPI.
- Enforce MIME, size, and page-count limits.
- Save PDFs outside source code paths used for application logic.
- Generate document identifiers and SHA-256 hashes.

### Extraction

- Detect whether the PDF is text-based or likely scanned.
- Extract multi-page tables using a primary engine.
- Remove repeated headers and non-table footer artifacts.
- Preserve PDF order unless a downstream deterministic sort is explicitly required.

### Normalization

- Map source headers to canonical fields.
- Preserve raw string values exactly.
- Normalize dates, currency strings, and decimal-comma quantities.
- Derive `tipo` only when deterministic from the extracted fields.

### Validation

- Run schema validation over every extracted row.
- Reconcile raw values against the source PDF extraction flow.
- Produce a machine-readable verification report.
- Record mismatch evidence with page, row, column, and raw values.

### Persistence

- Store document metadata and normalized rows in PostgreSQL.
- Keep enough provenance to re-run and audit extractions later.
- Make persistence idempotent so reruns do not create duplicate documents or transactions.

### Deduplication and Idempotency

The MVP must prevent duplicate financial data during repeated ingestion and future source expansion.

#### Document-Level Idempotency

- Every uploaded PDF must generate a SHA-256 hash.
- If a document with the same hash was already processed, the system must not insert a duplicate document record.
- Reprocessing behavior must be explicit and auditable.

#### Transaction-Level Deduplication

- Every normalized transaction row must have a deterministic fingerprint or natural key.
- The deduplication key must be based on stable business fields, not database-generated IDs.
- The first version should include the source system plus transaction-defining fields such as date, symbol, type, and monetary or quantity values.
- Persistence must use upsert-style semantics or an equivalent pre-insert deduplication check.

#### Cross-Source Separation

- PDF-derived portfolio transactions and API-derived market or reference data must not be stored as the same logical record type.
- Transaction data and market or price-history data must live in separate storage models.
- Future broker API or `yfinance` ingestion must include source provenance and deduplication rules before it is enabled.

#### Provenance Requirements

Every persisted record must preserve:

- source type
- source document ID or source request ID
- ingestion timestamp
- deterministic row fingerprint

This is required so duplicate detection, auditing, and future reconciliation remain explainable.

### Analytics

- Expose grouped portfolio views by ticker.
- Expose lot-level views for individual purchases.
- Compute initial KPIs such as capital invested, current value, unrealized return, and holding period.

### Frontend

- Show grouped rows by ticker with aggregate KPIs.
- Allow drill-down into individual lots or transactions.
- Prioritize correctness and auditability over design polish.

## Proposed Architecture

### Services

- `backend`: FastAPI application
- `db`: PostgreSQL
- `frontend`: React application

These services will run locally through Docker Compose.

### Backend Design Principles

- Keep the current FastAPI foundation and extend it with feature slices.
- Separate ingestion, extraction, parsing, validation, persistence, and analytics concerns.
- Use Pydantic for model contracts and row validation.
- Keep validation reports explicit and machine-readable.

### Data Flow

1. Upload PDF
2. Store file and hash metadata
3. Run preflight analysis
4. Extract raw tables
5. Normalize into canonical rows
6. Validate against schema and golden set expectations
7. Persist normalized records
8. Compute analytics
9. Serve frontend views

## Recommended MVP Module Boundaries

- `ingest`: file handling, storage, hashing, preflight checks
- `extract`: PDF engines and table extraction flow
- `parse`: header mapping and value normalization
- `validate`: schema checks, reconciliation, report generation
- `portfolio`: persistence and analytics
- `frontend`: grouped and lot-level portfolio views

## Success Metrics

The MVP is successful when:

- dataset 1 can be processed end-to-end without manual row editing
- extracted JSON matches the golden set for all required fields
- verification reports clearly explain every mismatch
- normalized rows are persisted in PostgreSQL
- grouped and transaction-level portfolio views are visible in the frontend
- baseline validation commands pass consistently in local development

## Risks

- PDF table extraction may be unstable across format changes.
- Some documents may require OCR fallback later.
- Locale-specific number formats may cause subtle normalization bugs.
- Market/reference API behavior may differ from transaction PDF semantics.
- KPI definitions can drift if formulas are not frozen early.

## Assumptions

- The initial PDF source is text-based and extractable without OCR.
- The first canonical schema is based on stock and ETF transaction statements.
- Historical broker/API data can be integrated without blocking the PDF ingestion MVP.

## Phase Order

1. PRD and contracts
2. Validation baseline
3. PDF extraction and golden-set reconciliation
4. Database persistence
5. Analytics API
6. Frontend grouped table
7. External broker API integration
8. Future phases: auth, AI, cloud deployment
