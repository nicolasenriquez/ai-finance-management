## Context

The repository already has a durable market-data persistence boundary and a working `yfinance` adapter, but current market-data behavior is still implementation-level rather than operational. The roadmap and backlog previously framed the remaining Phase 6 work in terms of broader provider expansion, but the current project decision is to treat `yfinance` as the deliberate near-term source because it is the fastest and cheapest way to populate market data while the product remains single-user and local-first.

That changes the next design priority. The next slice should not optimize for a generalized provider marketplace or broker-authenticated integration yet. It should optimize for one trustworthy operational path that can refresh the current supported symbol universe, preserve the existing fail-fast and non-mutation guarantees, and create a clean base for later valuation work.

## Goals / Non-Goals

**Goals:**
- Make `yfinance` refresh a first-class operational workflow rather than a helper-only service seam.
- Define one explicit full-refresh scope for the currently supported market-data universe.
- Preserve existing provider guarantees: deterministic snapshot identity, all-or-nothing ingest, fail-fast validation, and non-mutation of canonical and ledger truth.
- Provide one operator-facing execution path that can later be scheduled without redesigning the core orchestration.
- Align product and implementation docs so Phase 6 clearly reflects `yfinance` operationalization as the next approved slice.

**Non-Goals:**
- Building a multi-provider abstraction layer beyond what already exists implicitly in the current adapter boundary.
- Adding broker-authenticated credentials, account linking, or transaction import.
- Expanding `/api/portfolio/*` to market-value, unrealized, or snapshot-aware valuation responses.
- Adding frontend market-value cards or other UI changes tied to market-data analytics.
- Introducing distributed job infrastructure, queues, or cloud scheduler dependencies.

## Decisions

### 1. Keep `yfinance` as the only operational provider in this slice

The system should treat `yfinance` as the current production-facing market-data source for Phase 6 work instead of designing around future broker-authenticated providers now.

Why:
- It matches the current product constraint: time-efficient and cost-efficient market-data acquisition.
- It prevents overbuilding abstractions before there is a second real provider to justify them.
- It keeps implementation effort focused on operational trust rather than speculative extensibility.

Alternative considered:
- Build a broader provider-management layer now.
- Rejected because it widens scope without current product leverage and risks hiding `yfinance`-specific operational behavior behind premature abstraction.

### 2. Add one explicit manual refresh entrypoint for the supported universe

This slice should introduce one operator-facing refresh path that fetches the current supported symbol universe and persists it through the existing market-data service.

Why:
- The codebase currently has ingest orchestration but not a clear operational command/workflow.
- One explicit entrypoint is enough to make market data usable locally and is easy to validate.
- A manual path can later be invoked by a scheduler without changing persistence semantics.

Alternative considered:
- Add a scheduler first.
- Rejected because schedule infrastructure is not the current bottleneck; repeatable manual execution is the missing baseline.

### 3. Freeze full-refresh scope to one explicit supported-symbol contract

The full refresh should use one central supported-symbol source aligned with the current `dataset_1`-anchored market-data support contract, rather than discovering symbols opportunistically from provider responses.

Why:
- The repo already enforces a current supported symbol universe.
- Using one shared source prevents drift between validation, ingest, and operations.
- It keeps failures explicit when future ledger data introduces unsupported symbols.

Alternative considered:
- Derive symbols dynamically from whatever is in the database at runtime.
- Rejected because that can silently widen scope and blur the current support contract.

### 4. Preserve all-or-nothing refresh semantics for full-universe runs

A full refresh should fail as one unit if any requested symbol cannot be fetched or normalized safely.

Why:
- Existing provider ingest semantics are already whole-batch fail-fast.
- Partial success would create snapshots that look valid but are incomplete.
- Later valuation work depends on clear snapshot completeness semantics.

Alternative considered:
- Persist successful symbols and log skipped ones.
- Rejected because it weakens auditability and would require new completeness-state semantics not yet defined in the current model.

### 5. Make the operator result explicit and provenance-rich

The refresh workflow should return or log enough structured outcome data to prove what was requested, what snapshot was created, and whether the run fully succeeded or failed.

Why:
- Operational workflows need clearer evidence than helper functions.
- Provenance is already central to the market-data contract.
- This creates the base for future scheduled runs and analytics snapshot selection.

Alternative considered:
- Rely only on existing low-level service return values and logs.
- Rejected because the operator workflow needs one stable high-level success/failure contract.

### 6. Keep scheduling posture documented and invocation-ready, not overbuilt

This slice should make the refresh path callable by future automation, but not introduce cron, background workers, or external orchestration in the implementation unless the simplest local mechanism is clearly required.

Why:
- The product need is reliable refresh, not scheduler infrastructure.
- A callable operational seam preserves momentum and reduces implementation risk.
- Queue/scheduler choices are easier once real cadence needs exist.

Alternative considered:
- Add APScheduler/Celery-like infrastructure now.
- Rejected because it introduces unnecessary lifecycle and operational complexity for a local-first repository.

## Risks / Trade-offs

- [Risk] Keeping `yfinance` as the sole operational provider may lock some documentation language too tightly to one source. -> Mitigation: document that this is the current approved provider, while leaving later provider expansion as an explicit follow-up rather than implicit scope.
- [Risk] Full-refresh failure on one symbol can feel strict for operators. -> Mitigation: keep fail-fast semantics explicit and return/log the exact failing symbol/reason so the behavior is understandable and reproducible.
- [Risk] A fixed supported-symbol contract can drift from later persisted ledger reality. -> Mitigation: centralize the current support list and document that widening support requires a dedicated follow-up change.
- [Risk] A manual-only slice could be mistaken for “good enough forever.” -> Mitigation: document schedule-ready expectations and leave cadence/automation as explicit later work.
- [Risk] This slice could tempt early valuation expansion because market data becomes easier to populate. -> Mitigation: keep valuation APIs/frontend out of scope in proposal, specs, and tasks.

## Migration Plan

1. Add proposal, design, and spec artifacts for `yfinance` market-data operations.
2. Implement a dedicated refresh workflow and central supported-symbol resolution inside `app/market_data`.
3. Add unit/integration coverage for full-refresh scope, fail-fast semantics, and operator result behavior.
4. Update docs and changelog so Phase 6 reflects the `yfinance` operational path accurately.
5. Use the resulting seam as the base for a later market-enriched analytics proposal.

Rollback strategy:
- Revert the operational entrypoint, related orchestration/config updates, and docs together.
- Keep the current `market_data_snapshot` / `price_history` persistence boundary and low-level `yfinance` adapter intact if only the operational wrapper is rolled back.

## Open Questions

None blocking for proposal creation. The next decision after this slice is whether market-enriched analytics should consume only the latest successful snapshot or require explicit snapshot selection semantics.
