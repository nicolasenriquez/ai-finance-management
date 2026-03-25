# YFinance Financial Documents and Fundamentals Guide

## Purpose

This guide defines how to use `yfinance` fundamentals/financial-document style data as a research and enrichment layer without contaminating canonical transaction or ledger truth.

## Why This Matters

You requested support for importing relevant stock financial documents for deeper analysis.

That can add value when done with strict boundaries:

- fundamentals and statements enrich analysis context
- they do not replace broker transaction evidence
- they must remain provenance-tagged and disposable/rebuildable

## Boundary Rule (Critical)

- Canonical transaction truth remains PDF/API normalized transaction data.
- Ledger truth remains derived from canonical transaction events.
- `yfinance` fundamentals/documents are **analysis enrichment only** in this phase.

## Candidate Data Domains

Possible enrichment domains from `yfinance` docs/API surface:

- company profile/context metadata
- earnings history and estimates
- financial statements (income statement, balance sheet, cash flow)
- dividends/splits context for explanatory analytics

Treat these as provider snapshots, not accounting system-of-record inputs.

## Recommended Storage Direction (Future Slice)

If persisted later, use a dedicated enrichment boundary such as:

- `market_data_snapshot` lineage for fetch context
- separate enrichment table(s) keyed by:
  - `source_provider`
  - `instrument_symbol`
  - `statement_type`
  - `statement_period`
  - `as_of_date`
  - `snapshot_key`
  - `payload_hash`
  - `payload_json`

Do not store enrichment payloads in canonical transaction tables.

## Data Quality and Freshness Rules

- every payload must keep `fetched_at_utc` and `as_of_date` where available
- payload transformations must be deterministic
- missing fields must stay explicit (`null`), never inferred silently
- keep raw payload for audit/debug if used in derived summaries

## Analysis Usage Patterns

Valid uses:

- display context panels in future UI (for example earnings snapshot metadata)
- annotate derived analytics with explanatory context
- compare portfolio holdings against high-level fundamentals over time

Invalid uses in current scope:

- mutating lot cost basis or realized gain from provider fundamentals
- overriding ledger events with provider statement data
- claiming tax/accounting correctness from enrichment payloads alone

## Legal and Operational Notes

- follow provider usage terms and legal notices referenced by `yfinance`
- do not treat this source as guaranteed complete/authoritative accounting records
- plan for provider schema drift and missing fields

## Testing and Validation Expectations

For future implementation:

- fixture-based tests for payload parsing/mapping
- deterministic snapshot-key and payload-hash tests
- explicit failure tests for malformed or incomplete provider payloads
- no mandatory live-provider dependency in CI

## Recommended Phased Adoption

1. Phase A: read-only adapter + normalization contracts + fixture tests
2. Phase B: optional persistence boundary for enrichment payloads
3. Phase C: controlled analytics/UI consumption with explicit provenance labels

## References

Primary:

- https://ranaroussi.github.io/yfinance/index.html
- https://ranaroussi.github.io/yfinance/reference/index.html
- https://github.com/ranaroussi/yfinance

Secondary context:

- https://python-yahoofinance.readthedocs.io/en/latest/
