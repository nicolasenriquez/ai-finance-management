## Context

The repository now has a dedicated `app/market_data` slice with isolated persistence, fail-fast validation, and non-mutation guarantees for canonical and ledger truth. The next roadmap step is external provider integration, and current documentation already proposes `yfinance` as the first provider because it can validate the adapter boundary with low setup friction.

This change is not just a library import. It introduces a new external dependency, a provider-to-ingestion normalization boundary, and runtime behavior that must remain explicit when provider payloads are incomplete, symbol mapping is unsafe, or network/provider failures occur. The implementation must stay within the current ledger-first architecture and must not expand portfolio analytics, frontend valuation, or transaction ingestion scope.

The repo also already contains planning docs for this slice in the working tree:

- `docs/standards/market-data-provider-standard.md`
- `docs/guides/yfinance-integration-guide.md`
- `docs/guides/yfinance-financial-documents-and-fundamentals-guide.md`

Those docs establish the expected boundary and should be treated as the implementation guardrails for this change.

## Goals / Non-Goals

**Goals:**

- Add a first-class provider adapter path under `app/market_data` that fetches and normalizes `yfinance` market data into the existing ingestion service.
- Preserve current market-data write guarantees: provenance, deterministic snapshot identity, idempotency, supported-symbol validation, and non-mutation of canonical/ledger truth.
- Freeze first-slice price semantics so persisted `price_value` means one explicit provider-derived value instead of a mode that can drift across runs.
- Keep provider-specific behavior localized so future providers can be added without restructuring the core ingestion slice.
- Enforce fail-fast handling for malformed provider payloads, missing required timestamps or prices, and unsafe symbol mapping cases.
- Prove the adapter with deterministic unit and integration tests that do not require live-provider access in CI.

**Non-Goals:**

- Importing broker transactions or statements into canonical transaction storage.
- Expanding `/api/portfolio/*` into valuation, unrealized pricing, FX, or watchlist behavior.
- Adding background schedulers, cron-like refresh automation, or retention policies.
- Treating `yfinance` fundamentals or financial-document payloads as ledger or accounting truth.
- Generalizing to multiple providers in the same implementation slice.

## Decisions

### 1. Create a provider adapter module inside the existing market-data slice

The implementation should live under `app/market_data/` in a provider-focused module path such as `app/market_data/providers/yfinance.py`, with orchestration kept close to the existing market-data service boundary.

Why:

- It keeps provider-specific fetch and normalization logic out of persistence models and generic service code.
- It preserves the vertical-slice pattern already established by `app/market_data`.

Alternative considered:

- Call `yfinance` directly from `app/market_data/service.py`.
- Rejected because it would mix provider concerns with persistence/orchestration rules and make future provider additions harder to isolate.

### 2. Normalize provider responses into the existing ingestion contract instead of writing provider payloads directly

`yfinance` results should be converted into the current write schemas first, then persisted through the existing ingestion service.

Why:

- The repository already has validated uniqueness, provenance, and non-mutation rules in the ingestion boundary.
- Reusing that contract reduces drift between direct writes and provider-backed writes.

Alternative considered:

- Write `yfinance` payloads directly to `market_data_snapshot` / `price_history`.
- Rejected because it would duplicate validation logic and create a second persistence path with weaker guarantees.

### 3. Keep the first provider scope anchored to the current dataset_1 instrument set

The adapter should initially support the symbols already present in persisted `dataset_1` ledger truth, including dotted symbols such as `BRK.B`.

Why:

- The current repo has a concrete symbol universe and known edge cases to validate against.
- This keeps implementation scope honest and testable.

Alternative considered:

- Support any provider-returned symbol from day one.
- Rejected because it would broaden validation, mapping, and contract risk before the first adapter path is proven.

### 4. Make provider failures explicit and configuration minimal

The adapter should use explicit provider settings for timeout/retry behavior and fail clearly on provider/network or payload-shape defects.

Why:

- The repo rules favor fail-fast behavior over hidden fallbacks.
- External provider work becomes dangerous if outages or payload drift silently degrade into partial persistence.

Alternative considered:

- Add permissive fallbacks such as skipping malformed rows or silently accepting partial payloads.
- Rejected because it would weaken trust in persisted market-data snapshots.

### 5. Freeze first-slice price semantics and snapshot identity inputs

The first adapter slice should persist one explicit day-level price semantic and make `snapshot_key` include every fetch parameter that can change the resulting dataset.

First-slice expectations:

- persist raw day-level `Close` as `price_value`
- freeze `auto_adjust=False` so stored values do not silently change economic meaning across runs
- freeze `repair=False` in the first slice so persistence does not depend on provider-side reconstruction heuristics or false-positive repair behavior
- derive `currency_code` from explicit provider metadata when available, otherwise fail if it cannot be set safely
- use `trading_date` for the first day-level slice instead of `market_timestamp`, while keeping `snapshot_captured_at` timezone-aware in UTC
- include data-shaping inputs such as granularity, range/period basis, semantic flags, and requested-symbol set in `snapshot_key`
- encode `snapshot_key` in a bounded deterministic format that fits the current `String(128)` DB constraint instead of concatenating arbitrary raw request text

Why:

- Current persistence stores one `price_value` field, so semantic drift would produce valid-looking but inconsistent history.
- Current idempotency depends on deterministic snapshot identity.

Alternative considered:

- Defer price-semantic and snapshot-key choices to implementation time.
- Rejected because it would allow silent meaning changes and ambiguous idempotency behavior.

### 6. Keep provider batch persistence all-or-nothing

If one provider row in the requested batch cannot be normalized safely, the whole provider-backed ingest should fail before persistence instead of partially committing a subset of rows.

Why:

- The existing ingestion path is request-atomic and easier to reason about.
- Partial provider success would be hard to distinguish from complete snapshots in later analytics work.
- Missing requested symbols from the provider response are equivalent to an unsafe partial snapshot in the first slice.

Alternative considered:

- Persist valid rows and skip invalid ones.
- Rejected because it would create incomplete snapshots that look successful and weaken auditability.

### 7. Isolate provider fetches from the async request path

Provider library calls that are synchronous or blocking should be isolated behind an explicit runtime boundary so they do not stall the event loop.

Why:

- The existing market-data service boundary is async.
- Blocking provider calls can create timeout-like behavior and poor concurrency without obvious code-level errors.

Alternative considered:

- Call provider fetches directly in the async flow and rely on low traffic.
- Rejected because it creates non-obvious runtime risk and scales poorly.

### 8. Keep automated verification fixture-based, not live-provider dependent

The implementation should test adapter normalization and persistence using recorded or mocked payloads instead of requiring live `yfinance` access in CI.

Why:

- Live-provider tests are flaky and conflict with deterministic repo validation.
- The repo already treats validation as a delivery gate, not a best-effort check.

Alternative considered:

- Use live `yfinance` calls in automated tests.
- Rejected because network, provider availability, and upstream data changes would make validation non-reproducible.

## Risks / Trade-offs

- [Risk] `yfinance` is a convenience provider with upstream data/availability limits rather than a formal broker integration. -> Mitigation: keep the first adapter narrow, preserve provenance, and document provider limits explicitly.
- [Risk] Dotted or provider-variant symbols could be normalized incorrectly and break joins to ledger truth. -> Mitigation: anchor support to the current `dataset_1` symbol set and fail fast on unsafe mapping.
- [Risk] Direct provider integration could bypass existing idempotency and duplicate protections. -> Mitigation: route all writes through the current ingestion service contract instead of adding a second write path.
- [Risk] Blocking provider calls could stall async request handling and surface as confusing latency or timeout failures. -> Mitigation: isolate provider fetches behind an explicit runtime boundary and test the orchestration seam separately from provider I/O.
- [Risk] Different fetch flags could produce different price semantics under the same `snapshot_key`. -> Mitigation: freeze first-slice semantic choices and include all data-shaping inputs in snapshot identity.
- [Risk] Snapshot identity inputs could overflow the current `snapshot_key` column or drift across call sites. -> Mitigation: define one bounded snapshot-key builder in the adapter path and reuse it everywhere.
- [Risk] Adding external-provider code may tempt early valuation or UI scope expansion. -> Mitigation: keep current `/api/portfolio/*` and frontend contracts unchanged in this change.
- [Risk] Provider payload drift could silently degrade historical coverage or create partial snapshots. -> Mitigation: add explicit shape-validation tests, fixture-backed negative cases, and whole-batch rejection for unsafe rows.

## Migration Plan

1. Create proposal, spec, and tasks for the first provider-adapter capability.
2. Add `yfinance` dependency and provider config surface only as needed for the first adapter.
3. Implement adapter fetch + normalize flow and hand off to the existing market-data ingestion service.
4. Add deterministic unit/integration coverage for normalization, fail-fast behavior, and non-mutation guarantees.
5. Update docs and validation references to record the first provider adapter and its non-goals.

Rollback strategy:

- Revert the provider adapter module, dependency/config changes, and related tests/docs together.
- Keep the existing `app/market_data` persistence boundary intact even if the first provider implementation is rolled back.

## Open Questions

None blocking for proposal creation. Provider refresh cadence, background scheduling, and future paid/broker provider expansion remain explicitly deferred.
