## Context

Phase 6 now includes an implemented `yfinance` supported-universe refresh seam, but operational usage is not yet production-safe for day-to-day local execution. The service-level workflow currently depends on provider payload normalization that failed in live smoke testing (`AMD` surfaced as a trading-key label instead of a date key), and there is no standard command path to run `dataset_1` bootstrap plus market refresh in a single deterministic sequence.

The next slice should close this operational gap without expanding architecture: keep `yfinance` as the only active provider, preserve fail-fast semantics, and formalize local operator workflows as command-level entrypoints.

## Goals / Non-Goals

**Goals:**
- Remove the known runtime normalization failure mode in the `yfinance` adapter by handling supported payload shapes explicitly.
- Add local operator command entrypoints for `dataset_1` bootstrap, market refresh, and combined sync.
- Preserve existing ingestion and ledger contracts (idempotent where applicable, fail-fast, non-mutation boundaries).
- Produce deterministic run evidence so operators can verify what was executed and what succeeded or failed.

**Non-Goals:**
- Introducing broker-authenticated providers or multi-provider routing.
- Adding scheduler/queue infrastructure or distributed job orchestration.
- Exposing a new public market-data API router in this slice.
- Expanding portfolio analytics APIs to market-value/unrealized outputs.

## Decisions

### 1. Normalize `yfinance` close payloads using explicit shape branches

The adapter will treat runtime close payloads as a small validated shape set (series-like date index, tabular date-indexed forms, and explicitly rejected forms). Trading-date keys must always come from temporal index values, not symbol labels.

Why:
- The live failure shows current shape assumptions are not stable enough.
- Explicit shape handling is the smallest safe fix that preserves strict typing and fail-fast behavior.

Alternative considered:
- Coerce unknown shapes opportunistically and skip bad rows.
- Rejected because it can silently corrupt snapshot completeness semantics.

### 2. Implement operator workflows as thin local command wrappers over existing service seams

Add command entrypoints that orchestrate existing flows (`dataset_1` ingestion/persistence/rebuild and `refresh_yfinance_supported_universe`) rather than adding new persistence paths.

Why:
- Reuses tested contracts and keeps blast radius small.
- Delivers immediate operator value without API or infra expansion.

Alternative considered:
- Add a new public backend router first.
- Rejected for this slice to avoid widening trust boundaries before command workflow hardening is complete.

### 3. Keep combined sync strictly ordered and fail-fast

`data-sync-local` will run bootstrap first, then market refresh, and stop immediately on first failure.

Why:
- Deterministic ordering simplifies operator reasoning and incident diagnosis.
- Prevents misleading partial-success runs.

Alternative considered:
- Run both independently and summarize partial outcomes.
- Rejected because this weakens the contract for local readiness checks.

### 4. Return explicit run evidence for each command workflow

Each command should emit a typed summary including scope, provider/source identity, key counters, and status.

Why:
- Operators need reproducible evidence for troubleshooting and CI-like local validation.
- Aligns with existing structured logging and provenance requirements.

Alternative considered:
- Rely on unstructured console logs only.
- Rejected due to poor reproducibility and weaker auditability.

## Risks / Trade-offs

- [Risk] Over-coupling command wrappers to current local assumptions could complicate later scheduler integration. -> Mitigation: keep wrappers thin over service seams and avoid scheduler-specific behavior in this change.
- [Risk] Additional command entrypoints can drift from docs quickly. -> Mitigation: require docs and changelog updates in closeout tasks.
- [Risk] Provider payload drift can still introduce future shape variants. -> Mitigation: add explicit validation errors and targeted regression tests for shape handling.
- [Risk] Bootstrap command may fail due to local DB/env drift. -> Mitigation: require fail-fast error reporting and validation-baseline notes for environment blockers.

## Migration Plan

1. Add failing tests for the known `yfinance` payload-shape regression.
2. Implement adapter normalization hardening and keep strict fail-fast semantics.
3. Add local operator command wrappers and corresponding `just` recipes.
4. Add command-level tests and targeted integration proof for non-mutation/idempotent behavior.
5. Update docs/changelog and run OpenSpec + touched-scope validation.

Rollback strategy:
- Revert command-wrapper additions and `justfile` recipes as one unit.
- Revert adapter-shape changes if needed while preserving previous archived market-data operation contracts.

## Open Questions

None blocking for proposal readiness.
