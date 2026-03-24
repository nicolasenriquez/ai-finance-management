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
- Visualize grouped portfolio analytics by instrument with lot-level drill-down in a frontend.
- Use golden-set-driven validation so extraction quality is measurable and reproducible.

## Non-Goals

- No authentication or authorization in MVP.
- No GenAI or agentic features in MVP.
- No production cloud deployment in MVP.
- No novelty-driven or exploratory UI/UX expansion in MVP.
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
- Build a React frontend with grouped portfolio summary by instrument and lot-detail drill-down.

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

## Domain Model Direction

The long-term analytics model should be event-driven and ledger-first.

Core domain entities should converge toward:

- accounts
- institutions or brokers
- instruments
- source documents
- import jobs
- canonical transactions
- lots
- positions
- price history
- FX rates
- dividends and cash events
- corporate actions
- verification reports

The system of record is the canonical transaction ledger plus supporting provenance.
Portfolio snapshots, KPI tables, grouped views, and contribution reports are derived outputs and must be reproducible from canonical records.

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
- Keep transaction ledger tables separate from market data and derived analytics tables.

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
- Lots derived from transactions must remain stable across reruns of the same source data.

#### Cross-Source Separation

- PDF-derived portfolio transactions and API-derived market or reference data must not be stored as the same logical record type.
- Transaction data and market or price-history data must live in separate storage models.
- Future broker API or `yfinance` ingestion must include source provenance and deduplication rules before it is enabled.
- Broker-specific parsing logic must not leak into the canonical transaction schema.

#### Provenance Requirements

Every persisted record must preserve:

- source type
- source document ID or source request ID
- ingestion timestamp
- deterministic row fingerprint
- import batch or import job identifier

This is required so duplicate detection, auditing, and future reconciliation remain explainable.

### Market Data

- Current quotes and historical prices must be stored separately from the canonical transaction ledger.
- Market data refresh must be replaceable without mutating transaction records.
- Derived valuation metrics must always indicate the price timestamp or market data snapshot used.

### Accounting Policy

The project must explicitly freeze accounting rules before advanced analytics are treated as trusted.

The MVP and near-term roadmap must define:

- cost basis method for lot tracking
- realized gain and unrealized gain rules
- fee treatment
- dividend treatment
- FX conversion policy
- handling of splits and other corporate actions

These policies must be documented before broadening KPI coverage or performance claims.

### Analytics

- Expose grouped portfolio views by instrument symbol.
- Expose lot-level views for lot state and sell-side dispositions.
- Compute initial ledger-backed KPIs (`open_*`, `realized_*`, `dividend_*`).
- Make every lot-level contribution explainable from persisted ledger records.
- Distinguish between ledger-derived truth and presentation-oriented aggregates.
- Avoid analytics that depend on undocumented accounting assumptions.

### Frontend

- Show grouped rows by instrument symbol with ledger-backed KPIs.
- Allow drill-down into lot detail.
- Prioritize correctness and auditability over design polish.

## Importer and Normalizer Boundary

The system should formalize the boundary between source adapters and canonical data.

- broker or source adapters may emit raw or intermediate representations
- the normalizer is the only layer allowed to emit canonical transactions
- the canonical schema must remain broker-agnostic
- source-specific quirks should stay in adapters, mappers, or extraction rules
- normalization and validation must be deterministic and testable independent of a live source

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
- Keep the transaction ledger, market data, and derived analytics as separate concerns.
- Treat lots as first-class financial concepts rather than implicit UI groupings.

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
- grouped summary and lot-detail portfolio views are visible in the frontend
- baseline validation commands pass consistently in local development
- lot-level contribution output is explainable from source transactions
- reruns of the same source remain duplicate-safe

## Risks

- PDF table extraction may be unstable across format changes.
- Some documents may require OCR fallback later.
- Locale-specific number formats may cause subtle normalization bugs.
- Market/reference API behavior may differ from transaction PDF semantics.
- KPI definitions can drift if formulas are not frozen early.
- lot calculation can become inconsistent if accounting rules are not frozen explicitly.
- market data refresh may incorrectly influence ledger truth if storage boundaries are weak.

## Assumptions

- The initial PDF source is text-based and extractable without OCR.
- The first canonical schema is based on stock and ETF transaction statements.
- Historical broker/API data can be integrated without blocking the PDF ingestion MVP.

## Phase Order

1. PRD and contracts
2. Validation baseline
3. PDF extraction and golden-set reconciliation
4. Database persistence
5. Ledger-safe lot derivation and accounting policy freeze
6. Analytics API
7. Frontend grouped summary + lot detail
8. External broker API integration and market data enrichment
9. Future phases: auth, AI, cloud deployment
