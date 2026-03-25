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

## Current Repository Contract (Phase 6 Market-Data Boundary)

As of 2026-03-24, the implemented contract is:

- `source_document` -> `import_job` -> `canonical_pdf_record` -> `portfolio_transaction` / `dividend_event` / `corporate_action_event` -> `lot` / `lot_disposition`
- Supported canonical event families: `trade`, `dividend`, `split`
- Frozen accounting policy version: `dataset_1_v1`
- Sell matching method: FIFO lot matching
- Trade basis fields: buy uses `aporte_usd`; sell proceeds use `rescate_usd`
- Dividends are income events and do not mutate lot basis
- Splits adjust open-lot quantity and per-share basis proportionally while preserving total lot basis
- Fee, FX, and unsupported corporate-action handling remain explicit unsupported concerns in v1
- Portfolio analytics summary endpoint: `GET /api/portfolio/summary`
- Portfolio analytics lot-detail endpoint: `GET /api/portfolio/lots/{instrument_symbol}`
- Analytics responses expose explicit `as_of_ledger_at` and ledger-only KPI v1 fields
- Lot-detail symbol matching is deterministic (`trim + uppercase`) with explicit unknown-symbol failure
- Market-data persistence boundary: `market_data_snapshot` -> `price_history` via `app/market_data`
- Market-data write boundary enforces explicit source provenance, timezone-safe snapshot timestamps, canonical symbol forms, and deterministic symbol/time-key idempotency
- Market-data read boundary exists for persisted symbol price history and remains internal-only (no public market-data API route yet)
- Local operator market-data commands are available (`data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`) and remain command-level (no public market-data router in this slice)

Current boundary:

- Market data (`market_data_snapshot`, `price_history`, future `fx_rate`) is separate and not part of ledger truth.
- Market-data refresh does not mutate canonical records, ledger events, lots, lot dispositions, dividends, or corporate-action truth.
- Portfolio analytics responses remain ledger-only and do not read market data yet.
- Market-data-dependent valuation and unrealized pricing metrics remain deferred.

## Why This Guide Exists

The project needs a clear distinction between:

- what becomes canonical financial truth
- what stays source-specific import logic
- what is derived analytics convenience
- which external repositories are worth studying and why

This guide is not just a list of concepts.
It is a decision document for implementing a self-hosted personal investment dashboard with:

- transaction history
- current pricing
- position views
- lot-level contribution analysis
- future support for dividends, FX, and corporate actions

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

## Recommended Minimal Domain Model

For this project, the most relevant minimum direction is:

- `broker_account`
- `source_document`
- `import_job`
- `instrument`
- `portfolio_transaction`
- `cash_event`
- `dividend_event`
- `corporate_action`
- `lot`
- `lot_disposition`
- `price_history`
- `fx_rate`
- `position_snapshot`
- `verification_report`

Recommended interpretation:

- `portfolio_transaction` is the canonical trade ledger, not a UI view model
- `lot` is derived from canonical trade activity plus accounting policy
- `price_history` and `fx_rate` are separate market data concerns
- `position_snapshot` is a rebuildable analytics cache, not the source of truth

For the VOO per-buy contribution use case, the critical chain is:

`source_document` -> `import_job` -> `portfolio_transaction` -> `lot` -> `price_history` -> analytics

If that chain is explainable and reproducible, the system stays trustworthy.

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

Dataset 1 v1 is now explicitly frozen with FIFO, dividend-income isolation, split proportional adjustment, and explicit unsupported fee/FX inference.

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

## Reference Selection Criteria

External references are only useful if they are close to this project's target shape.

Prioritize repositories that show some combination of:

- canonical transaction storage
- holdings or lot derivation from transactions
- market data separated from ledger truth
- portfolio performance or P&L analytics
- database-backed workflows instead of browser-only local state
- realistic import, deduplication, and reprocessing behavior

Do not overweight:

- polished dashboards without a clear ledger model
- watchlists presented as portfolio systems
- local-storage-only apps with weak persistence semantics
- repos that show charts but not transaction accounting

## Reference Review

The previous report was not strong enough because it mostly named repositories without making the evaluation criteria explicit.
This section fixes that by stating:

- the repository URL
- why it is relevant to this exact problem
- what to study in it
- why it should not be treated as the primary model

### Tier 1: Core References

These are the only repositories that should materially influence the ledger and analytics design.

#### 1. Ghostfolio

Repository: https://github.com/ghostfolio/ghostfolio

Why it makes the list:

- mature self-hosted wealth product with real breadth across accounts, transactions, positions, and analytics
- useful benchmark for how a serious end-to-end portfolio platform is organized
- strongest reference here for studying domain boundaries at production scale

What to study:

- portfolio domain modeling
- separation between imported data, portfolio state, and analytics
- backend module boundaries
- user-facing KPI and reporting structure

Why it is not enough by itself:

- it is broader than the current project
- its stack and product scope are much larger than the intended MVP
- it is a benchmark, not the most copyable implementation path

Verdict:

- best overall benchmark
- best for architecture and product shape
- not the best first template for implementation

#### 2. Doughbox

Repository: https://github.com/alxjpzmn/doughbox

Why it makes the list:

- closest match to the desired architecture direction for this repository
- centered on statement imports, normalized storage, deduplication, and database-backed analytics
- aligns directly with the need for canonical transactions plus separate quote refresh workflows

What to study:

- import pipeline structure
- canonical transaction storage
- deduplication and re-import handling
- separation of portfolio events from quote data

Why it matters most here:

- this project needs ledger-first correctness more than dashboard breadth
- Doughbox is the strongest reference for transaction truth, not just presentation

Verdict:

- most relevant backend reference
- strongest inspiration for ingestion plus storage design
- should heavily influence the ledger pipeline

#### 3. Stock-P-L

Repository: https://github.com/willychang21/Stock-P-L

Why it makes the list:

- closer to a realistic solo-builder implementation than larger wealth platforms
- uses a stack and scope that are easier to map to an incremental MVP
- focused on trade-history import and P&L rather than generic market dashboards

What to study:

- practical FastAPI service boundaries
- trade import workflows
- realized and unrealized P&L views
- market-data integration for an MVP

Why it is not the primary benchmark:

- smaller and less proven than Ghostfolio
- narrower in accounting depth than Portfolio Performance

Verdict:

- best copyable MVP reference
- strong implementation guide once the ledger boundaries are decided

#### 4. Portfolio Performance

Repository: https://github.com/portfolio-performance/portfolio

Why it makes the list:

- strongest source in this list for accounting depth and edge-case thinking
- valuable even though it is not a web-first architecture reference
- useful for validating portfolio calculation policy before claiming correctness

What to study:

- performance-calculation edge cases
- importer and reconciliation behavior
- treatment of splits, dividends, and cost basis concerns

Why it is not a foundation repo:

- less relevant for backend web architecture
- stronger as a finance-logic reference than as an application structure model

Verdict:

- best accounting-depth reference
- should inform calculation policy and test cases

#### 5. Ascend

Repository: https://github.com/rajatpatel92/portfolio-app

Why it makes the list:

- useful source of ideas for advanced analytics modules after the ledger is stable
- relevant for multi-currency, performance dashboards, and investor-facing metrics

What to study:

- XIRR and performance views
- dividend and gain dashboards
- higher-level analytics modules

Why it ranks below the others:

- weaker as a primary architecture model
- better for analytics inspiration than for transaction-truth design

Verdict:

- future-facing analytics reference
- useful after ingestion and lot accounting are already trustworthy

### Tier 2: Secondary References

These repositories are relevant, but they should not drive the canonical ledger design.

#### Stonks Overwatch

Repository: https://github.com/ctasada/stonks-overwatch

Keep it for:

- multi-broker consolidation ideas
- privacy-first local product direction
- plugin and adapter thinking

Do not rely on it for:

- authoritative ledger design
- accounting-policy depth

#### Visualfolio

Repository: https://github.com/benvigano/visualfolio

Keep it for:

- domain and entity inspiration
- account and dashboard UX ideas

Do not rely on it for:

- production-readiness assumptions
- core architecture decisions

#### Investment Dashboard

Repository: https://github.com/nmfretz/investment-dashboard

Keep it for:

- frontend layout and chart ideas
- lighter portfolio visualization patterns

Do not rely on it for:

- canonical transaction persistence
- database-backed lot analytics

#### Wealth Warden

Repository: https://github.com/nootey/wealth-warden

Keep it for:

- self-hosted personal finance framing
- simplicity and automation ideas

Do not rely on it for:

- investment-ledger architecture
- lot-level contribution analysis

## What To Copy Versus What To Keep Local

Use external repositories to validate patterns, not to outsource local architecture decisions.

Copy ideas for:

- import pipeline boundaries
- idempotent ledger ingestion
- separation of trades from market data
- rebuildable analytics snapshots
- portfolio KPI decomposition

Keep local and explicit:

- canonical schema definitions
- accounting policy choices
- source provenance rules
- duplicate detection policy
- golden test cases for financial correctness

## Recommended Study Order

For this project, the highest-value study sequence is:

1. Ghostfolio
2. Doughbox
3. Stock-P-L
4. Portfolio Performance
5. Ascend

Reason:

- `Ghostfolio` shows the broad production benchmark
- `Doughbox` is closest to the desired ingestion and storage architecture
- `Stock-P-L` is closest to a practical MVP implementation path
- `Portfolio Performance` deepens accounting correctness
- `Ascend` helps after the ledger and pricing pipeline are already sound

## Architecture Implication From References

The reference review points to a clear implementation direction for this repository:

- use `Ghostfolio` to validate broad product boundaries
- use `Doughbox` to shape the canonical ingestion and deduplication pipeline
- use `Stock-P-L` to keep the MVP implementation practical
- use `Portfolio Performance` to define accounting-policy tests
- use `Ascend` only after the ledger and pricing model are stable

In short:

- `Doughbox` should influence schema and ingestion most
- `Ghostfolio` should influence architecture and UX direction most
- `Portfolio Performance` should influence correctness most
- `Stock-P-L` should influence implementation pragmatism most

## Decision Summary

For this repository, the target direction should remain:

- ledger-first
- import-safe and duplicate-safe
- lot derivation from canonical transactions
- market data isolated from transaction truth
- analytics rebuilt from ledger plus prices

The most relevant external references are not merely "portfolio dashboards."
They are repositories that show transaction truth, derivation boundaries, and explainable analytics.
