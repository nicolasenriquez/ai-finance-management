## Context

The repository already has three pieces in place that were previously missing:

- ledger-backed grouped portfolio analytics in `app/portfolio_analytics/`
- persisted market-data snapshots and price history in `app/market_data/`
- operator workflows that populate persisted `yfinance` snapshot data without mutating ledger truth

Current state:

- `GET /api/portfolio/summary` is implemented, but it returns only ledger-only KPI fields.
- The frontend still describes the summary as "No inferred market value" because no price-backed valuation contract exists yet.
- `app/market_data/service.py` already exposes an internal read path for persisted symbol price history, but portfolio analytics does not consume it.
- Product docs now place market-enriched KPI expansion after the delivered provider and operational work, which makes this the next coherent Phase 6 change.

Constraints:

- Keep ledger truth authoritative and read-only.
- Do not introduce public market-data routes in this change.
- Do not add FX-sensitive valuation behavior; current scope remains USD-only market enrichment.
- Keep valuation provenance explicit by naming the persisted market-data snapshot or timestamp used.
- Avoid mixed-time valuation semantics across symbols in the same grouped summary response.

## Goals / Non-Goals

**Goals:**

- Enrich grouped portfolio summary rows with bounded market-value and unrealized KPI fields.
- Use one explicit persisted market-data snapshot as the valuation source for one summary response.
- Expose pricing provenance clearly in the response contract.
- Fail explicitly when required open-position symbols do not have safe pricing coverage in the selected snapshot.
- Update backend tests, API schemas, frontend contract/copy, and docs for the new analytics boundary.

**Non-Goals:**

- Expanding lot-detail responses with price-backed valuation.
- Adding public market-data API routes.
- Rebuilding ledger state or mutating market-data state during analytics reads.
- Adding FX conversion, multi-currency valuation, or broker-authenticated pricing sources.
- Adding scheduler/queue infrastructure or changing operator refresh semantics.

## Decisions

### 1. Keep the first market-enriched slice summary-only

The change will enrich `GET /api/portfolio/summary` and leave lot-detail contract changes for a later slice if they are needed.

Why:

- The grouped summary is the current product surface that most directly benefits from valuation fields.
- Summary-only scope keeps Phase 6 tight and avoids broadening the API/frontend/test blast radius unnecessarily.
- Lot-detail can continue to explain ledger truth without coupling Phase 6 completion to additional pricing UI work.

Alternative considered:

- Enrich summary and lot detail together.
- Rejected because it broadens the contract and verification surface before the summary valuation contract is proven.

### 2. Use one consistent persisted market-data snapshot per summary response

Market-enriched KPIs will be computed from one selected `market_data_snapshot`, not from independently chosen latest rows per symbol.

Why:

- The PRD requires explicit pricing snapshot or timestamp provenance for valuation metrics.
- A single snapshot avoids mixed-time portfolio values that would be hard to explain or test.
- It preserves a clean fail-fast boundary: either the summary has coherent pricing coverage for open positions, or it rejects the request explicitly.

Alternative considered:

- Use the latest persisted price row per symbol regardless of snapshot identity.
- Rejected because it creates mixed-time valuation semantics and weakens provenance clarity.

### 3. Require complete coverage for open positions in the selected snapshot

If an instrument with `open_quantity > 0` is missing safe pricing rows in the selected snapshot, the summary request will fail explicitly instead of silently omitting valuation fields or mixing fallback rows.

Why:

- The repository favors explicit failure over masked degradation.
- Partial valuation would make portfolio totals appear more complete than they are.
- This keeps the summary contract trustworthy for downstream frontend rendering and tests.

Alternative considered:

- Return partial pricing coverage with null fields on affected open positions.
- Rejected because it hides an upstream readiness/data-coverage problem inside the analytics response.

### 4. Keep enriched valuation fields bounded to current USD-compatible semantics

The first market-enriched KPI set will add price-backed fields only where current ledger + market-data contracts support them safely, such as:

- latest close price in USD-compatible semantics
- market value
- unrealized gain/loss
- unrealized gain/loss percentage

Why:

- Current product docs explicitly defer FX-sensitive valuation.
- The persisted price contract already carries currency code and day-level close semantics, which is enough for a bounded USD-compatible slice.
- This preserves a clean future expansion path for FX-aware valuation without pretending it is solved now.

Alternative considered:

- Add broader performance/return fields immediately.
- Rejected because that would entangle this slice with deferred FX and accounting-policy questions.

### 5. Reuse internal market-data read paths with a focused analytics-side helper

Implementation may add a targeted read helper for selecting the latest consistent snapshot with required symbol coverage, while keeping the read path internal to backend services.

Why:

- The analytics slice needs batch snapshot selection semantics, not a public market-data route.
- Reusing the existing persistence boundary keeps provider logic out of analytics.
- A focused helper keeps the read contract explicit without overloading current single-symbol history listing.

Alternative considered:

- Query price history ad hoc directly inside analytics service without a market-data helper.
- Rejected because snapshot-selection logic would become harder to reuse and reason about.

## Risks / Trade-offs

- [Risk] Recent refresh evidence may still expose coverage gaps for some symbols. -> Mitigation: fail explicitly for missing open-position prices and keep snapshot selection/test fixtures deterministic.
- [Risk] Summary schema expansion will ripple into frontend contract tests and copy. -> Mitigation: keep the change summary-only and update frontend messaging in the same slice.
- [Risk] Choosing one consistent snapshot may reject requests more often than per-symbol latest-row logic. -> Mitigation: prefer trust and provenance clarity over partial valuation convenience.
- [Risk] Closed positions could be over-modeled with unnecessary price fields. -> Mitigation: keep valuation fields bounded to open-position semantics and document null behavior for rows with no open quantity.

## Migration Plan

1. Add fail-first tests for enriched grouped summary formulas, snapshot selection, and explicit coverage failures.
2. Extend analytics and market-data read helpers to select one consistent persisted snapshot for required open-position symbols.
3. Expand response schemas and summary route/service logic with pricing provenance plus bounded valuation fields.
4. Update frontend API schemas, summary rendering copy/tests, and documentation.
5. Run targeted backend/frontend validation and record the contract change in `CHANGELOG.md`.

Rollback strategy:

- Revert the enriched summary schema and service/query changes.
- Leave persisted market-data tables and operator workflows unchanged because this change is read-only over existing storage.

## Open Questions

None.
