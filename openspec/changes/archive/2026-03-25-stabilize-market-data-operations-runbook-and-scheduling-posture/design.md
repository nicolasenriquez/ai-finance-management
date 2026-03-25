## Context

The repository already exposes local operator commands for dataset bootstrap and `yfinance` refresh, and Phase 6 now depends on those commands becoming trustworthy enough to serve as the operational bridge to later market-enriched analytics. Recent closeout evidence showed that the current path is close but not fully stable: deterministic automated coverage passes, yet a live smoke run can still fail on environment-dependent provider payload details, and the repo does not yet define one crisp runbook/evidence contract for treating those outcomes as success or blocker evidence.

This design therefore treats the next slice as an operational hardening change, not a product-expansion change. The implementation should preserve the current market-data boundaries, keep scheduler infrastructure out of scope, and make the existing command-level workflows trustworthy enough that later changes can assume a stable refresh posture.

## Goals / Non-Goals

**Goals:**
- Freeze one approved runbook and smoke-evidence contract for `market-refresh-yfinance` and `data-sync-local`.
- Harden the current provider normalization path for the approved live day-level temporal variants needed by operational refreshes.
- Keep scheduling posture explicit and invocation-ready on top of the existing command surfaces.
- Preserve existing fail-fast, all-or-nothing, deterministic, and non-mutation guarantees.
- Update docs, validation guidance, and changelog expectations so operational blockers are visible and actionable.

**Non-Goals:**
- Adding cron, queue, worker, or hosted scheduler infrastructure.
- Introducing a public market-data route or new API trigger surface.
- Broadening market-data scope to broker-authenticated providers or multi-provider orchestration.
- Expanding analytics, valuation KPIs, or frontend market-data UX.
- Weakening fail-fast behavior by silently coercing unknown live payload shapes.

## Decisions

### 1. Treat operational stabilization as both a documentation and minimal runtime-hardening change

The change should not be documentation-only because the repository already captured a real live smoke blocker tied to the approved `yfinance` path. The slice should therefore pair explicit runbook/evidence rules with the smallest runtime/provider hardening needed to support approved live operational refresh behavior.

Why:
- A runbook without a trustworthy live path is not enough for later planning confidence.
- The known blocker is narrow and operationally relevant rather than a broad architectural failure.
- This keeps the change aligned with roadmap sequencing without jumping ahead to analytics expansion.

Alternative considered:
- Documentation-only runbook update.
- Rejected because it would leave the known live smoke blocker unresolved and would not make the change truly implementation-ready for later consumers.

### 2. Keep the command surfaces unchanged and make them the schedule-ready contract

The approved invocation posture should stay anchored to the existing `just` recipes and module CLI entrypoints. The change should document how future automation would call those same seams rather than creating a second contract now.

Why:
- The current commands already encode the intended execution order and fail-fast semantics.
- A future scheduler should reuse a stable operational seam instead of redefining refresh behavior.
- This avoids overbuilding automation infrastructure before cadence requirements are real.

Alternative considered:
- Introduce a scheduler abstraction or background job entrypoint now.
- Rejected because it adds lifecycle complexity without improving the current local-first operator baseline.

### 3. Harden only explicitly approved live temporal variants in the provider adapter

Provider hardening should be constrained to live `yfinance` response variants that preserve the current day-level semantics and can be mapped safely into the existing `trading_date` contract. Unknown variants should still fail explicitly.

Why:
- The repo already values fail-fast behavior over permissive inference.
- The current blocker suggests a narrow temporal-key mapping issue, not a need for broad parsing heuristics.
- Limiting accepted variants keeps behavior testable and auditable.

Alternative considered:
- Add broad payload coercion or row-skipping fallback behavior.
- Rejected because it would blur operational safety and weaken snapshot completeness guarantees.

### 4. Treat blocked live smoke outcomes as first-class operational evidence

The runbook and validation guidance should explicitly allow a blocked live smoke run to count as evidence of current operational status when the rejection is captured precisely and linked to the correct stage/reason.

Why:
- External provider/network conditions are environment-dependent and not fully reproducible in CI.
- Operators need a defined way to distinguish “workflow is broken” from “workflow rejected unsafe input correctly.”
- This keeps closeout evidence honest without pretending every environment can produce a successful live smoke run.

Alternative considered:
- Require only successful live smoke outcomes.
- Rejected because it would make environment-dependent blockers hard to report accurately and would encourage optimistic or missing evidence.

## Risks / Trade-offs

- [Risk] The live smoke blocker may reflect more than one response-shape issue. -> Mitigation: start with explicit investigation tasks that capture the exact approved variants before hardening code.
- [Risk] Runbook guidance could drift from actual command behavior. -> Mitigation: anchor docs to the existing `just` and module CLI commands and verify them during touched-scope validation.
- [Risk] Accepting additional live temporal variants could accidentally widen semantics. -> Mitigation: constrain accepted variants to day-level trading-date mappings and keep unknown variants fail-fast.
- [Risk] Schedule-ready wording could be misread as implementing scheduling. -> Mitigation: keep non-goals explicit in proposal, specs, tasks, and docs.
- [Risk] Existing command-doc changes in this branch are unrelated to the change scope. -> Mitigation: keep implementation and validation notes for this change scoped to `openspec/changes/stabilize-market-data-operations-runbook-and-scheduling-posture` and the eventual touched runtime/docs areas only.

## Migration Plan

1. Investigate the current live smoke blocker and freeze the approved operational evidence contract.
2. Harden the minimal provider/operation path needed for approved live day-level refresh behavior.
3. Add deterministic tests covering the approved live temporal variants and blocker evidence behavior.
4. Update runbook, validation, roadmap/backlog/decision docs, and changelog expectations.
5. Re-run touched-scope validation plus one explicit manual smoke path, recording either success evidence or blocker evidence.

Rollback strategy:
- Revert the provider/operation hardening and documentation updates together.
- Preserve the existing market-data persistence boundary, local commands, and deterministic automated coverage from prior changes if only this stabilization slice is rolled back.

## Open Questions

None blocking for proposal creation. The implementation investigation should confirm the minimal approved live temporal-key variants before code changes are finalized.
