## 0. Investigation

- [ ] 0.1 Confirm the exact Phase 4 analytics boundary from the roadmap, PRD, ADRs, ledger guide, and current OpenSpec specs before coding
Notes: Keep this change inside analytics service plus API scope. Do not expand into market-data ingestion, pricing snapshots, or frontend implementation.
Notes: Confirm that KPI v1 stays ledger-only and explainable from `portfolio_transaction`, `dividend_event`, `lot`, and `lot_disposition`.
- [ ] 0.2 Diagnose blast radius across router registration, query patterns, response schemas, validation docs, and future frontend dependencies
Notes: Explicitly map affected areas in `app/main.py`, the new `app/portfolio_analytics/` slice, validation expectations, and docs that describe Phase 4 boundaries.
Notes: Confirm whether any shared schemas are truly cross-slice or whether analytics should remain self-contained inside its feature slice.

## 1. Contract and failing tests

- [ ] 1.1 Add failing unit tests for grouped summary analytics formulas from existing ledger truth
Notes: Cover grouped rows by `instrument_symbol` and assert ledger-only KPI fields such as `open_quantity`, `open_cost_basis_usd`, `realized_gain_usd`, and dividend totals.
- [ ] 1.2 Add failing unit tests for lot-detail analytics output and unknown-symbol rejection
Notes: Verify explainable lot rows plus linked disposition detail for an existing symbol, deterministic symbol normalization (trim + case-insensitive), and explicit client-facing failure for a missing symbol.
- [ ] 1.3 Add failing route/integration tests for summary and lot-detail endpoints
Notes: Route tests should lock response shape, status codes, and `as_of_ledger_at` presence; integration tests should prove analytics are computed from persisted ledger state rather than PDF reprocessing.

## 2. Analytics schemas and service

- [ ] 2.1 Define typed analytics schemas for grouped summary, lot detail, and route responses
Notes: Keep response models explicit and stable for the future frontend; include `as_of_ledger_at` and do not add price-dependent fields in this change.
- [ ] 2.2 Implement grouped summary query/service logic from ledger and lot tables
Notes: Compute only ledger-supported KPI fields, emit explicit `as_of_ledger_at`, and keep analytics read-only over persisted truth.
- [ ] 2.3 Implement lot-detail query/service logic with explainable disposition history
Notes: Reuse persisted lot and sell-side disposition data rather than re-deriving accounting logic inside analytics, with deterministic symbol normalization.

## 3. API routes and application wiring

- [ ] 3.1 Add portfolio analytics FastAPI routes for grouped summary and lot detail
Notes: Use a portfolio-facing route surface and explicit client errors for unsupported symbol requests.
- [ ] 3.2 Register the analytics router in the application entrypoint and align structured logging
Notes: Logging should follow the repo event naming standard and keep request-level context explicit; analytics routes must not invoke rebuild operations.

## 4. Validation and documentation

- [ ] 4.1 Run targeted unit, route, and integration validation for the analytics slice
Notes: Expected checks include targeted `pytest`, `ruff`, `black --check --diff`, `bandit`, `mypy`, `pyright`, and `ty`; include DB-backed integration checks if analytics tests depend on real ledger rows.
- [ ] 4.2 Update roadmap-adjacent guides and validation references for the new analytics API boundary
Notes: Reflect that grouped and lot-detail analytics APIs are implemented while market-data-dependent valuation remains deferred.
- [ ] 4.3 Update `CHANGELOG.md` and confirm OpenSpec artifacts are archive-ready after implementation
Notes: Record the analytics API as the prerequisite backend contract for the later frontend MVP.
