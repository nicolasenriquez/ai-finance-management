## Context

The repository already supports manual `yfinance` refresh with fail-fast behavior, and now has a versioned symbol universe (`core_refresh_symbols`, `starter_100_symbols`, `starter_200_symbols`). Current operational refresh still targets a single fixed scope, which limits controlled onboarding for real-data testing. We need a minimal extension that lets operators widen scope deliberately without introducing scheduler infrastructure or weakening non-mutation guarantees.

## Goals / Non-Goals

**Goals:**
- Add explicit refresh scope selection (`core`, `100`, `200`) for operator refresh workflows.
- Keep `core` as default to preserve backward compatibility and low-risk baseline behavior.
- Reuse the existing versioned symbol-universe contract as the only scope source.
- Preserve all existing fail-fast, all-or-nothing ingest, and non-mutation guarantees.
- Make run evidence scope-aware so real-data onboarding is auditable stage by stage.

**Non-Goals:**
- Adding scheduler/queue/cron infrastructure.
- Adding or exposing public market-data API routes.
- Expanding provider strategy beyond current `yfinance` operational path.
- Changing ledger/canonical persistence boundaries.
- Expanding valuation or frontend market-value behavior.

## Decisions

### 1. Introduce one explicit refresh-scope mode at orchestration boundaries

Add a strict scope mode (`core`, `100`, `200`) to the market refresh orchestration path and propagate it through data-sync command workflows.
Freeze one typed contract for this selector: `refresh_scope_mode: Literal["core", "100", "200"]`.

Why:
- Operators need deterministic staged onboarding behavior.
- One typed selector is simpler than ad hoc symbol-list overrides.
- Keeps behavior easy to test and audit.

Alternative considered:
- Free-form symbol inputs at CLI level.
- Rejected because it weakens determinism and bypasses the versioned universe contract.

### 2. Resolve symbols only from `symbol_universe.v1.json`

Scope resolution will map directly to existing universe fields:
- `core` -> `core_refresh_symbols`
- `100` -> `starter_100_symbols`
- `200` -> `starter_200_symbols`

Why:
- Existing contract already enforces subset guarantees and portfolio minimum inclusion.
- Prevents hidden scope drift from provider-side discovery.

Alternative considered:
- Build scope dynamically from live provider screens.
- Rejected because results are unstable and harder to validate deterministically.

### 3. Keep fail-fast semantics unchanged per selected scope

Each selected scope remains all-or-nothing: if one symbol fails normalization/fetch requirements, the refresh run fails explicitly.

Why:
- Preserves current safety posture and snapshot integrity expectations.
- Avoids ambiguous partial-success behavior.

Alternative considered:
- Best-effort persistence for successful symbols.
- Rejected because it breaks current full-refresh contract clarity.

### 4. Make structured outcome evidence scope-aware

Refresh/sync outcomes and logs should include selected scope mode and requested symbol count so staged onboarding runs can be compared and audited.
Freeze minimum evidence fields:
- successful market refresh: `refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`
- blocked market refresh: existing fail-fast fields (`status`, `stage`, `status_code`, `error`) plus `refresh_scope_mode`
- combined local sync: nested market-refresh evidence preserves the same minimum scope-aware fields

Why:
- Real-data testing needs explicit evidence per stage (`core -> 100 -> 200`).
- Keeps runbook closeout deterministic.

Alternative considered:
- Keep evidence unchanged and infer scope indirectly.
- Rejected because inference is fragile and increases operator ambiguity.

## Risks / Trade-offs

- [Risk] Larger scopes (`100`/`200`) increase provider/network failure probability. -> Mitigation: keep default `core`, require staged smoke evidence, and preserve explicit fail-fast blocker reporting.
- [Risk] CLI/API surface drift between market-data and data-sync layers. -> Mitigation: add unit tests for propagation and defaults across service + CLI boundaries.
- [Risk] Documentation and roadmap state diverge from runtime behavior. -> Mitigation: update runbook/product docs and changelog in the same change.
- [Risk] Operators jump directly to `200` without proving `core` stability. -> Mitigation: define runbook recommendation and validation ordering (`core` first) while still allowing explicit override.

## Migration Plan

1. Add typed refresh-scope support in market-data service orchestration with `core` default.
2. Propagate scope through data-sync service and CLI entrypoints.
3. Add `just` recipe argument support for refresh scope where relevant.
4. Add deterministic unit/integration coverage for scope resolution, propagation, and fail-fast behavior.
5. Update validation/runbook docs with staged smoke procedure (`core -> 100 -> 200`).

Rollback strategy:
- Revert scope-selector plumbing while keeping existing `core` refresh path intact.
- Preserve symbol-universe file and generator artifacts as they are backward-compatible with `core`-only execution.

## Open Questions

None blocking for planning. Implementation should confirm exact evidence fields to include in success/failure payloads without breaking existing consumers.
