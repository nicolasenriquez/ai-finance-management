## Context

The repository now has a stable ledger-first pipeline:

- canonical PDF records persist in PostgreSQL
- ledger events and lots derive from persisted canonical truth
- portfolio analytics exposes read-only grouped and lot-detail responses
- frontend release-readiness work is complete and archived

The next roadmap phase is market data and external broker integration, but the codebase does not yet define a durable market-data boundary. Product and architecture docs already require that market data remain separate from ledger truth, that quote refresh never mutates canonical or ledger records, and that future analytics declare the pricing snapshot they use.

There is also a workflow-quality gap: `openspec validate --specs --all` is currently red because the legacy `pdf-ingestion` and `pdf-preflight-analysis` main specs still use delta-style formatting instead of the required `Purpose` + `Requirements` structure. That issue is not product behavior, but it is relevant because it weakens the repository's planning and archive gates for the next phase.

## Goals / Non-Goals

**Goals:**

- Define a first-class market-data ingestion capability with explicit storage and provenance boundaries.
- Keep market-data writes independent from canonical transaction, ledger, lot, and analytics-truth tables.
- Require idempotent refresh semantics so repeated quote or historical-price ingestion does not create ambiguous duplicates.
- Freeze the first supported market-data symbol universe to the instruments already present in persisted `dataset_1` ledger truth so implementation starts from a real, testable scope.
- Use native PostgreSQL and the current repository architecture before considering TimescaleDB or provider-specific optimizations.
- Restore global OpenSpec spec validation as part of the change closeout so the new phase does not advance on top of a known workflow defect.

**Non-Goals:**

- Expanding portfolio analytics to market-value, unrealized gain, or FX-sensitive KPI endpoints.
- Shipping new frontend views for price history, valuation, or watchlist behavior.
- Committing to one broker API provider contract beyond the boundary and provenance rules needed for ingestion.
- Fetching live provider data as part of this slice.
- Adopting TimescaleDB, background scheduling, or retention automation in this first slice.

## Decisions

### 1. Create a dedicated backend feature slice for market data

The implementation should live in its own vertical slice (for example `app/market_data/`) with models, schemas, service logic, and tests rather than being embedded into `portfolio_analytics` or `portfolio_ledger`.

Why:

- Market data is its own durable concern with different refresh cadence and deduplication rules.
- Keeping it separate preserves the repository's ledger-first architecture and makes future broker-adapter work easier to localize.

Alternative considered:

- Add price-history tables inside `portfolio_analytics`.
- Rejected because it would blur the boundary between durable source data and derived analytics responses.

### 2. Use native PostgreSQL tables first, not TimescaleDB

The first market-data slice should use ordinary PostgreSQL tables, constraints, and indexes.

Why:

- Repository guidance already says TimescaleDB is optional and future-facing.
- The immediate goal is a correct storage boundary and idempotent refresh semantics, not time-series scale optimization.

Alternative considered:

- Introduce TimescaleDB immediately for `price_history`.
- Rejected because it adds runtime and migration complexity before there is evidence that native PostgreSQL is insufficient.

### 3. Treat refresh provenance as mandatory, not optional metadata

Every persisted market-data row should preserve enough information to answer:

- which provider/source produced it
- which instrument it describes
- which timestamp or trading date it represents
- when the system ingested it
- which refresh batch or snapshot it belongs to

Why:

- Future analytics must be able to declare which snapshot was used.
- Refresh idempotency and debugging become untrustworthy if provenance is only implied.

Alternative considered:

- Store only symbol + price and infer the rest from context.
- Rejected because it undermines auditability and makes duplicate handling provider-specific and fragile.

### 4. Keep this slice storage-focused and read-boundary-focused

This change should define ingestion, persistence, and retrieval boundaries needed for later analytics consumption, but it should not broaden the current `/api/portfolio/*` KPI contract.

Why:

- Roadmap sequencing puts market-data storage before valuation expansion.
- It keeps the blast radius localized to data boundaries, migrations, and tests.

Alternative considered:

- Bundle valuation API changes into the same proposal.
- Rejected because it would mix storage-boundary work with accounting and frontend contract expansion.

### 5. Freeze the first symbol-universe contract to current dataset_1 ledger truth

The first slice should prove symbol handling for the instruments already present in `dataset_1` ledger truth rather than claiming support for an abstract future market universe.

Current dataset_1 symbol set:

- `AMD`
- `APLD`
- `BBAI`
- `BRK.B`
- `GLD`
- `GOOGL`
- `HOOD`
- `META`
- `NVDA`
- `PLTR`
- `QQQM`
- `SCHD`
- `SCHG`
- `SMH`
- `SOFI`
- `SPMO`
- `TSLA`
- `UUUU`
- `VOO`

Why:

- The repository already has a concrete, persisted instrument universe to anchor tests and schema assumptions.
- Dotted tickers such as `BRK.B` make it unsafe to postpone symbol-shape rules until provider integration.
- This keeps scope honest without forcing premature provider selection.

Alternative considered:

- Leave initial symbol coverage unspecified until the future broker API change.
- Rejected because it would allow implementation to drift into generic assumptions that may not hold for current ledger truth.

### 6. Fix OpenSpec spec-format drift as part of change closeout

The change should include tasks to rewrite the existing `pdf-ingestion` and `pdf-preflight-analysis` main specs into valid main-spec structure without changing their intended requirements.

Why:

- Global OpenSpec validation is part of repository workflow quality.
- Leaving it red weakens confidence in future `/plan`, `/validate`, and archive steps.

Alternative considered:

- Ignore the failing specs because they are unrelated to market data behavior.
- Rejected because the failure is already a documented repo-wide validation defect and will continue to pollute future work.

## Risks / Trade-offs

- [Risk] Provider contract details may still be partially unknown at proposal time. -> Mitigation: keep the first slice boundary-oriented and provider-agnostic; define provenance and idempotency requirements before adapter-specific details.
- [Risk] Symbol handling may silently break for real instruments if the first slice assumes only simple uppercase tickers. -> Mitigation: anchor tests and validation to the existing `dataset_1` symbol set, including dotted tickers such as `BRK.B`.
- [Risk] Market-data schema can become over-designed before real query patterns exist. -> Mitigation: stay additive and minimal; model only quote/history fields that are part of the stable write and read boundary.
- [Risk] Adding market-data tables may tempt early valuation features. -> Mitigation: keep portfolio analytics contract unchanged in this proposal and call valuation expansion a separate future change.
- [Risk] Repairing legacy OpenSpec spec formatting could accidentally change archived intent. -> Mitigation: rewrite only structure, preserve requirement meaning, and validate with `openspec validate --specs --all`.

## Migration Plan

1. Add proposal-driven specs and tasks for the new market-data capability.
2. Implement minimal database schema and service boundary for price-history / quote-style persistence with strict provenance, dataset_1 symbol coverage, and deduplication rules.
3. Add targeted tests proving refresh idempotency, symbol-shape handling, and non-mutation of canonical and ledger truth.
4. Update docs and validation baseline references for the new boundary.
5. Repair legacy OpenSpec main-spec structure and rerun repo-wide spec validation before archive.

Rollback strategy:

- Revert the market-data slice, migration, and docs as one change if schema or boundary assumptions prove wrong.
- Do not mix valuation or frontend work into this change, so rollback remains storage-boundary-focused.

## Open Questions

None blocking for proposal creation. Provider selection, refresh cadence, and future analytics formulas remain deferred to later changes, while the current slice is explicitly anchored to `dataset_1` ledger symbols and storage-boundary behavior.
