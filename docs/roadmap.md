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

## Phase 3: Portfolio Analytics API

- Build portfolio aggregation endpoints.
- Build lot-level transaction endpoints.
- Define initial KPI formulas.
- Add unit and integration coverage for analytics logic.

## Phase 4: Frontend MVP

- Add React frontend container to Docker Compose.
- Build grouped table by ticker.
- Add drill-down view for lots and transactions.
- Connect frontend to analytics APIs.

## Phase 5: External Broker API Integration

- Integrate broker API for historical/reference data.
- Reconcile API-driven data with PDF-driven records where needed.
- Expand analytics scope using the additional data.

## Deferred Phases

- authentication and authorization
- AI or agentic enrichment
- Supabase migration
- production cloud deployment
