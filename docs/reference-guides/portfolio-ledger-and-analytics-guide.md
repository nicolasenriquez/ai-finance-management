# Portfolio Ledger And Analytics Guide

## Purpose

This guide defines the preferred architecture direction for portfolio tracking after extraction and validation are stable.

It is intended to help human developers and AI agents make consistent decisions about:

- transaction storage
- lot derivation
- market data separation
- analytics boundaries
- financial calculation policy

## Guiding Principle

Keep the portfolio model ledger-first.

The system of record is the canonical transaction history plus provenance.
Current holdings, grouped KPI views, and lot contribution reports are derived outputs.

## Core Boundaries

### 1. Source Adapters

Source adapters are responsible for source-specific behavior.

Examples:

- PDF extraction flow
- broker API clients
- future CSV importers

Rules:

- adapters may emit raw or intermediate representations
- adapters must preserve source provenance
- adapters must not define the canonical portfolio schema

### 2. Canonical Ledger

The canonical ledger is the trusted financial record.

Target concepts:

- account
- broker or institution
- source document
- import job
- canonical transaction
- cash event
- dividend event
- corporate action event

Rules:

- ledger records must be idempotent
- ledger records must have deterministic fingerprints or natural keys
- rerunning the same source must not duplicate ledger truth
- provenance must remain queryable

### 3. Lots and Positions

Lots and positions are derived from ledger events.

Rules:

- lots should be explainable from buy, sell, split, and related events
- positions should be reconstructable from lots and transactions
- lot logic must follow an explicit accounting policy

### 4. Market Data

Market data is separate from the ledger.

Examples:

- current quotes
- historical prices
- FX rates

Rules:

- market data refresh must not mutate ledger records
- analytics must indicate which pricing snapshot or timestamp they use
- missing market data must degrade clearly, not silently

### 5. Derived Analytics

Derived analytics include:

- grouped portfolio views
- lot-level contribution reports
- realized and unrealized gain views
- KPI summaries
- snapshots for frontend performance

Rules:

- derived analytics must be reproducible from ledger plus market data
- derived tables or caches are disposable and rebuildable
- analytics formulas must not rely on undocumented assumptions

## Preferred Entity Direction

As the project grows, the schema should move toward concepts such as:

- `source_document`
- `import_job`
- `portfolio_transaction`
- `cash_event`
- `dividend_event`
- `corporate_action`
- `lot`
- `position_snapshot`
- `price_history`
- `fx_rate`
- `verification_report`

The exact table names can change, but the boundary between ledger, market data, and derived analytics should remain stable.

## Accounting Policy Requirements

Before advanced analytics are treated as trusted, the project must explicitly document:

- cost basis method
- realized gain method
- unrealized gain method
- fee treatment
- dividend treatment
- FX conversion policy
- split and corporate action handling

This policy should be frozen before claiming correctness for portfolio contribution, performance, or tax-sensitive analytics.

## Testing Implications

Extraction golden sets are necessary but not sufficient.

The project should also add financial golden cases for:

- lot contribution
- realized gain and unrealized gain
- fee handling
- dividend handling
- FX-sensitive calculations
- duplicate-ingestion behavior

These tests should validate finance rules independently of PDF extraction quality.

## Repository Implementation Guidance

When adding new features:

- keep source-specific logic in adapters or extraction modules
- keep canonical validation in schemas and normalizers
- keep persistence duplicate-safe
- keep quote refresh and pricing isolated from transaction truth
- keep analytics explainable from base records

## External Reference Mapping

Use external repositories by strength:

- `doughbox` for unified storage, imports, deduplication, and quote separation
- `ghostfolio` for domain modeling and mature analytics architecture
- `Stock-P-L` for pragmatic MVP transaction-first implementation
- `Portfolio Performance` for accounting depth and financial edge cases
- `Ascend` for future advanced analytics ideas

These references should improve local decisions, not replace local source-of-truth documents.
