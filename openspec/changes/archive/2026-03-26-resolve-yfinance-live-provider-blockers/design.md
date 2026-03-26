## Context

Phase 6 already has a working `yfinance` adapter, a supported-symbol universe, staged refresh scopes (`core`, `100`, `200`), and local operator entrypoints for refresh and combined sync. Recent changelog and roadmap evidence shows that the remaining instability is not architectural; it is concentrated in concrete live-provider blocker patterns such as empty-history responses and missing currency metadata for real symbols during smoke runs.

In current execution, local workflow hardening is also in scope because operational validation and smoke checks are run repeatedly during this phase. The repository now carries runtime and test database safety concerns in `just` command surfaces and `.env` defaults; those safeguards must be captured as part of this change contract rather than left as undocumented side effects.

The current repository constraints still apply:

- canonical, ledger, lot, dividend, and corporate-action truth must remain untouched by market-data refresh
- automated tests must stay deterministic and avoid live-provider dependence
- `core` refresh is the portfolio-minimum operational scope and cannot silently degrade
- scheduler/queue infrastructure, public market-data routes, and market-enriched analytics remain out of scope

## Goals / Non-Goals

**Goals:**

- Define one explicit recovery contract for known live `yfinance` blocker patterns before the system classifies a symbol as failed.
- Preserve strict fail-fast behavior for `core` and any required-portfolio symbol across all staged scopes.
- Allow `100/200` refresh runs to complete only when remaining failures are outside the required-portfolio set and inside the approved blocker categories.
- Standardize operator evidence so staged live runs clearly show what was retried, what still failed, and whether completion was strict or bounded-partial.
- Keep planning and implementation localized to provider adapter, market-data orchestration, data-sync entrypoints, tests, and operational docs.
- Keep retry and pacing behavior explicit and conservative by default (`1` retry, configurable linear backoff, configurable per-symbol request spacing) while preserving override support through settings.
- Keep local runtime/test database workflows isolated so `just dev` and test recipes do not silently share one database URL.

**Non-Goals:**

- Adding market-enriched analytics or valuation APIs
- Introducing scheduler, queue, cron, or worker infrastructure
- Expanding to broker-authenticated or multi-provider integrations
- Relaxing fail-fast behavior for unsupported payload semantics, required symbol coverage, or canonical/ledger mutation boundaries
- Introducing cross-environment deployment hardening beyond local workflow safeguards

## Decisions

### Decision: Use bounded symbol-scoped recovery before final provider failure classification

The adapter/service path will treat the observed live blockers as approved recovery candidates rather than immediate terminal failures. Recovery remains narrow and explicit: alternative metadata/history access paths or one retry pass may be used only for the already-observed blocker classes needed by current operations.

Why this over broader graceful degradation:

- It addresses real Phase 6 blockers without weakening the repository's fail-fast posture.
- It keeps the recovery contract auditable and testable.
- It avoids normalizing arbitrary provider weirdness into silently accepted behavior.

Alternative considered:

- Treat every live-provider anomaly as a hard blocker forever. Rejected because Phase 6 explicitly requires operational stabilization before analytics expansion, and the observed blockers appear narrow enough to handle safely.

### Decision: Keep retry and pacing conservative by default but configurable through settings

The operational default will remain conservative (`max_retries=1` with existing bounded backoff and explicit `request_spacing_seconds` between symbol requests), and both controls stay configurable through `Settings` for controlled tuning.

Why this over fixed hardcoded timings:

- It reduces live-provider pressure by default for onboarding scopes.
- It avoids freezing one operational profile when provider conditions may vary.
- It remains transparent and testable in typed config and deterministic unit coverage.

Alternative considered:

- Hardcode fixed retry/sleep behavior in service loops. Rejected because tuning would require code changes and increase operational friction.

### Decision: Keep scope-sensitive completion rules in the operations layer, not the adapter

The adapter should classify or surface symbol-level failure causes, but the service/orchestration layer decides whether a run blocks or completes. `core` remains all-or-nothing. `100/200` may complete only when all failed symbols are outside the required-portfolio set and all failures belong to the approved blocker classes after recovery is exhausted.

Why this over embedding scope logic in the adapter:

- Scope policy is an operator contract, not a provider-normalization concern.
- It preserves clean layering between provider fetch/normalize logic and orchestration semantics.
- It keeps future providers reusable under the same operations contract.

Alternative considered:

- Let the adapter drop unrecoverable symbols automatically for starter scopes. Rejected because it hides policy in the wrong layer and risks widening tolerated behavior accidentally.

### Decision: Standardize typed run evidence around retries, failed symbols, and completion mode

Successful and bounded-partial refresh runs will expose the retry attempt set and the final failed-symbol set alongside the existing scope and snapshot evidence. Blocked runs continue to expose the fail-fast payload contract, with enough detail for operators to distinguish required-coverage blockers from tolerated non-portfolio gaps.

Why this over relying only on logs:

- OpenSpec roadmap and validation docs already treat structured evidence as the operational contract.
- CLI and sync workflows need machine-readable outputs for reproducible smoke reporting.
- Logs alone are insufficient for closeout and staged onboarding comparison.

Alternative considered:

- Keep current evidence unchanged and rely on changelog notes for nuance. Rejected because the remaining Phase 6 question is precisely about operational interpretation of live outcomes.

### Decision: Include local runtime/test database isolation safeguards in this change boundary

Local workflow guards (`DATABASE_URL` runtime safety checks, dedicated `TEST_DATABASE_URL`, and isolated migration/test execution paths) are treated as in-scope because they directly affect trustworthiness of operational evidence and test outcomes during Phase 6 closeout.

Why this over deferring to a separate workflow change:

- Current implementation already contains these safeguards and they influence validation posture now.
- Phase-level evidence quality degrades if runtime and test DB targets can drift together.
- Capturing them here keeps proposal, implementation, and validation history aligned.

Alternative considered:

- Split workflow guards into a separate proposal later. Rejected for this branch because it would leave immediate scope/accountability mismatch between OpenSpec artifacts and actual diff.

## Risks / Trade-offs

- [Risk] Recovery logic could quietly widen beyond the intended blocker classes. -> Mitigation: define the approved blocker classes explicitly in specs, cover them with deterministic tests, and keep unsupported provider semantics fail-fast.
- [Risk] Partial completion for `100/200` could be mistaken for portfolio-safe completeness. -> Mitigation: preserve strict required-portfolio gating and include failed-symbol diagnostics directly in typed results and docs.
- [Risk] Adapter and operations responsibilities could blur. -> Mitigation: keep symbol failure classification in provider/service fetch seams and final completion policy in refresh orchestration.
- [Risk] Live-provider behavior may change again outside the observed blocker classes. -> Mitigation: retain explicit blocker evidence for unknown patterns and keep the change scoped so later proposals can extend the contract deliberately if needed.
- [Risk] Request pacing may lengthen full refresh runtime for 100/200 scopes. -> Mitigation: keep pacing configurable and bounded in settings with explicit defaults documented in runbooks.
- [Risk] Workflow guardrails may block existing local setups that do not define isolated test DB URLs. -> Mitigation: document `.env` requirements and fail with explicit actionable messages.

## Migration Plan

1. Lock the desired behavior with targeted unit and integration tests for provider blocker classification, scope-sensitive completion, and CLI/data-sync evidence.
2. Update adapter/service/data-sync code and schemas in the smallest slice needed to satisfy the new contract.
3. Refresh operator and product docs to record the approved blocker classes, completion rules, and smoke evidence expectations.
4. Update local workflow docs and examples (`README`, `.env.example`, `just` guard behaviors) so runtime/test DB isolation expectations are explicit.
5. Run deterministic validation first, then one manual staged smoke sequence (`core -> 100 -> 200`) to capture post-change evidence.
6. If the change must be rolled back, preserve existing refresh seams and revert blocker-handling/rate-control defaults plus workflow guards together to avoid mixed operational posture.

## Open Questions

- None. The current change is intentionally scoped to the already-documented live-provider blocker patterns and does not depend on unresolved architecture decisions.
