## Context

The repository has completed the PDF ETL pipeline, canonical persistence, and portfolio-ledger foundation for dataset 1. The next gap is not more ingestion work, but a stable application-facing analytics boundary that can expose grouped portfolio summaries and lot-level drill-down from already-derived ledger truth.

Current state:

- Canonical records persist in PostgreSQL and are replayable from stored PDF assets.
- Portfolio ledger derivation produces `portfolio_transaction`, `dividend_event`, `corporate_action_event`, `lot`, and `lot_disposition`.
- Accounting policy `dataset_1_v1` is frozen and explainable.
- No analytics service or analytics FastAPI routes exist yet.
- Market data (`price_history`, `fx_rate`) is explicitly deferred to a later phase.

Constraints:

- Keep the implementation inside Phase 4 analytics API scope.
- Preserve vertical slice architecture by adding a dedicated `app/portfolio_analytics/` feature.
- Preserve fail-fast behavior and do not invent price-dependent values without market data.
- Keep analytics read-only over ledger truth; this slice must not mutate canonical or ledger tables.
- Keep analytics freshness semantics explicit: this API reads persisted ledger state and does not trigger ledger rebuilds.

## Goals / Non-Goals

**Goals:**

- Define a minimal analytics API contract that is computed directly from ledger and lot state.
- Add a grouped portfolio summary endpoint suitable for an MVP frontend table.
- Add a lot-level detail endpoint suitable for drill-down and explainability.
- Freeze a first KPI set that is fully supported by current ledger data.
- Add tests that prove analytics formulas and route behavior from database truth.

**Non-Goals:**

- Adding market data tables, quote ingestion, or price-history refresh.
- Returning current valuation, unrealized market value, or price-dependent percentage returns.
- Introducing analytics caches, snapshots, or materialized views.
- Changing portfolio-ledger derivation semantics or accounting-policy rules.
- Building the frontend in this change.

## Decisions

### 1. Add a dedicated `portfolio_analytics` feature slice

Analytics behavior will live in `app/portfolio_analytics/` with `schemas.py`, `service.py`, `routes.py`, and `tests/`.

Why:

- Keeps Phase 4 work isolated from the already-frozen ledger implementation.
- Matches the repo's vertical slice architecture.
- Avoids overloading `portfolio_ledger` with presentation-facing aggregation concerns.

Alternative considered:

- Add analytics helpers into `app/portfolio_ledger/`.
- Rejected because it mixes system-of-record derivation with read-oriented API aggregation logic.

### 2. Compute analytics directly from existing ledger tables without new persistence

The first implementation will query and aggregate `lot`, `lot_disposition`, `portfolio_transaction`, and `dividend_event` directly.

Why:

- This is the smallest change that produces trustworthy analytics now.
- It preserves the ledger-first architecture and keeps analytics rebuildable.
- It avoids introducing premature snapshot/caching infrastructure before query patterns are proven.

Alternative considered:

- Add `position_snapshot` or precomputed analytics tables immediately.
- Rejected because the MVP does not yet have query-scale evidence justifying that complexity.

### 3. Freeze KPI v1 to ledger-supported fields only

The analytics API will expose only metrics that can be computed from current ledger truth:

- `open_quantity`
- `open_cost_basis_usd`
- `open_lot_count`
- `realized_proceeds_usd`
- `realized_cost_basis_usd`
- `realized_gain_usd`
- `dividend_gross_usd`
- `dividend_taxes_usd`
- `dividend_net_usd`

Why:

- These fields are explainable from current tables and accounting policy.
- They avoid fake precision or hidden assumptions about unavailable market prices.
- They still provide useful portfolio insight and unblock frontend/API progress.

Alternative considered:

- Include current value, unrealized gain, or total return placeholders.
- Rejected because those require market data and would either be null-heavy or misleading.

### 4. Expose two GET endpoints under one portfolio analytics router

The planned route shape is:

- `GET /api/portfolio/summary`
- `GET /api/portfolio/lots/{instrument_symbol}`

Why:

- This is minimal and aligned with the roadmap's grouped view plus drill-down requirement.
- It gives the future frontend a stable API shape without over-designing filters or pagination yet.
- It keeps the contract easy to test and easy to explain.

Alternative considered:

- Use `/api/portfolio-analytics/...` or `/api/analytics/...`.
- Rejected because `portfolio` is the clearer product-facing resource boundary for the MVP.

### 5. Keep analytics read-only and fail fast on unsafe assumptions

The analytics service will reject unsupported query conditions explicitly and will not backfill missing market-dependent fields.

Why:

- Preserves the repo's fail-fast principle.
- Avoids silent fallbacks that would make financial output look more complete than it is.

Alternative considered:

- Return inferred or dummy market-value fields.
- Rejected because it violates the trust boundary established by the PRD and ADRs.

### 6. Add explicit response consistency metadata with one ledger `as_of` timestamp

Both grouped summary and lot-detail responses will include one `as_of_ledger_at` field representing the ledger state time used to compute the response.

Why:

- Prevents ambiguity when frontend compares grouped and drill-down views.
- Makes analytics outputs auditable and easier to debug.
- Avoids hidden race assumptions about data freshness.

Alternative considered:

- Omit explicit response timestamp metadata.
- Rejected because the API would not clearly communicate which persisted ledger state was used.

### 7. Define deterministic symbol normalization and unknown-symbol behavior

The lot-detail endpoint will normalize symbol input by trimming whitespace and matching case-insensitively, while preserving one canonical uppercase symbol in response payloads. Unknown symbols will return an explicit not-found client error.

Why:

- Prevents client friction for common input variants (`VOO`, `voo`, ` voo `).
- Removes ambiguity between "no lots" and "symbol not found".
- Keeps endpoint behavior deterministic for tests and frontend integration.

Alternative considered:

- Case-sensitive symbol matching with empty success payloads.
- Rejected because it increases accidental misses and weakens fail-fast semantics.

### 8. Keep analytics request path independent from rebuild side effects

Analytics routes will never run `rebuild_portfolio_ledger_from_canonical_records` internally. Rebuild remains an explicit upstream operation.

Why:

- Preserves read-only behavior and predictable latency for analytics requests.
- Avoids hidden write side effects inside GET-like flows.
- Keeps operational responsibilities separated: rebuild for state preparation, analytics for state consumption.

Alternative considered:

- Auto-trigger rebuild when analytics detects stale/missing derived rows.
- Rejected because it mixes write concerns into read endpoints and can mask upstream pipeline issues.

## Risks / Trade-offs

- [Risk] Summary queries may need non-trivial joins across lots, dispositions, sells, and dividends. -> Mitigation: keep KPI scope narrow, start with targeted tests, and add only the joins required by the documented fields.
- [Risk] Future market-data work may force response-schema expansion. -> Mitigation: make v1 analytics explicitly ledger-only and document that valuation fields are deferred.
- [Risk] Route naming could drift when the frontend starts. -> Mitigation: freeze the minimal route surface in spec now and treat additional filters/views as later additive changes.
- [Risk] Analytics correctness may be undermined if it duplicates accounting logic instead of reading ledger truth. -> Mitigation: compute realized figures from persisted ledger/lot tables rather than re-deriving accounting policy in the analytics slice.
- [Risk] Frontend compares endpoints that were computed from different moments in persisted state. -> Mitigation: include explicit `as_of_ledger_at` in both summary and lot-detail responses.
- [Risk] Analytics requests may become an accidental write path if rebuild is invoked implicitly. -> Mitigation: keep rebuild invocation out of analytics routes and test read-only behavior explicitly.

## Migration Plan

1. Add the new `portfolio_analytics` slice and route registration.
2. Implement grouped summary service/query logic from existing ledger tables.
3. Implement lot-detail service/query logic from existing ledger tables.
4. Add unit tests for analytics aggregation and integration tests for route behavior.
5. Update roadmap/guides/validation references and `CHANGELOG.md`.

Rollback strategy:

- Remove the analytics router and feature slice.
- No schema rollback is required because this change should not introduce database tables or migrations.

## Open Questions

None. The change is intentionally scoped to ledger-only analytics so market-data and valuation decisions remain deferred.
