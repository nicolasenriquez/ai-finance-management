## Context

`phase-j` delivered the workspace shell and copilot presentation polish, and `phase-i` delivered AI/ML contract layering. The DCA opportunity flow is functionally available, but key policy controls are still hardcoded in frontend session defaults, which weakens transparency and operator control.

The provided DCA tutorial adds another governance requirement: recommendations should be grounded in one stable DCA source of truth (SOT) rather than ad-hoc prompt phrasing. In particular, recommendation quality should consistently reflect:

- baseline cadence discipline (regular DCA)
- double-down trigger discipline (drawdown threshold + history eligibility)
- fundamentals verification posture (proxy + explicit caveat)
- concentration/risk framing and review cadence

Constraints:

- Keep read-only copilot boundaries and non-advice posture unchanged.
- Keep deterministic opportunity ranking formula and bounded request limits.
- Preserve strict typed contracts across Python schemas and frontend Zod schemas.
- Follow fail-first test posture for behavior changes.

## Goals / Non-Goals

**Goals:**

- Make DCA policy inputs explicit and user-visible from composer controls to backend request payload.
- Preserve deterministic and safe classification behavior, including no `double_down_candidate` result when 52-week eligibility cannot be evaluated.
- Encode one DCA SOT assessment framing for opportunity outputs and follow-up prompts.
- Upgrade recommendation bubbles into operation-aware, business-grade prompt catalogs for chat and DCA flows.
- Keep copilot presentation ready for post-dashboard personal assistant usage (docked + expanded, evidence-first, transparency-oriented).
- Close governance with tests, type gates, and documentation updates.

**Non-Goals:**

- Introducing trade execution, rebalance automation, or financial-advice guarantees.
- Changing the opportunity scoring formula weights.
- Adding persistent memory or vector-store behavior to copilot.
- Introducing full autonomous tool approval workflows in this change.

## Decisions

### Decision: Treat DCA controls as explicit request contract fields, not hidden defaults

The composer and session layer will expose DCA knobs directly and submit user-selected values through the typed request contract.

Rationale:

- Improves explainability and operator trust.
- Makes behavior reproducible across sessions and tests.
- Avoids drift between UI intent and backend scoring behavior.

Alternatives considered:

- Keep hidden defaults in frontend session state: rejected because it obscures policy and makes tuning brittle.

### Decision: Keep strict 52-week gating as a deterministic precondition for double-down classification

`double_down_candidate` remains forbidden unless full 52-week history coverage is present and threshold conditions are evaluable.

Rationale:

- Prevents false confidence from partial market history.
- Matches fail-fast contract discipline for incomplete critical inputs.

Alternatives considered:

- Infer 52-week proxy from shorter windows: rejected due to semantic ambiguity and unstable classification quality.

### Decision: Introduce one DCA SOT assessment envelope for opportunity workflows

Opportunity responses and follow-up prompts will use one stable assessment framing:

1. DCA baseline discipline
2. Double-down eligibility and threshold result
3. Fundamentals proxy outcome and caveat
4. Concentration/risk-control implications
5. Next-check and monitoring prompt

Rationale:

- Aligns recommendation language with deterministic policy outputs instead of free-form style drift.
- Keeps narration auditable and grep-friendly for tests and operations.
- Converts tutorial guidance into enforceable product behavior.

Alternatives considered:

- Keep free-form recommendation style per prompt template: rejected due to unstable interpretation quality.

### Decision: Enforce operation-aware, portfolio-business recommendation bubbles

Suggestion chips will be curated per operation (`chat` vs `opportunity_scan`) and prioritize allocation, concentration, benchmark context, drawdown governance, and capital-deployment framing.

Rationale:

- Aligns prompt guidance with passive-investor and portfolio-governance outcomes.
- Reduces low-signal or generic question suggestions.

Alternatives considered:

- One generic suggestion pool for all operations: rejected because it dilutes analytical relevance.

### Decision: Preserve docked + expanded assistant model with event-transparency semantics

This change keeps the assistant UX posture as:

- desktop docked lateral panel
- mobile full-screen presentation
- expanded route for deep review
- event-aware response lifecycle semantics (`start`/loading, streaming intent, `tool_call`, `end`)

Rationale:

- Keeps continuity with existing workspace behavior while preparing for the post-dashboard personal assistant.
- Matches transparency patterns used in modern full-stack AI agent templates where users inspect generation/tool phases (reference: `https://github.com/vstorm-co/full-stack-ai-agent-template`).

Alternatives considered:

- Single full-page copilot only: rejected because it weakens workspace continuity.

## Risks / Trade-offs

- [Higher UI density in composer controls] -> Keep DCA controls conditionally visible for `opportunity_scan` only and preserve compact/mobile ergonomics.
- [Validation mismatch between frontend/backend decimal handling] -> Keep strict schema parity and add fail-first request-shape tests.
- [Recommendation copy regresses into generic phrasing] -> Freeze business-grade prompt catalogs and SOT envelope acceptance language in tests.
- [Users infer prescriptive advice from confidence language] -> Keep explicit non-advice caveats and deterministic reason-code evidence visible.
- [SOT asks exceed available user-financial context] -> Return explicit insufficiency caveats instead of fabricating personal-finance assumptions.

## Migration Plan

1. Add fail-first tests for DCA control visibility, payload propagation, 52-week gating behavior, and SOT envelope expectations.
2. Implement typed contract wiring in backend schemas/service and frontend schemas/session/composer.
3. Implement operation-aware recommendation bubble catalogs aligned with SOT DCA framing.
4. Keep workspace presentation deterministic across docked/expanded/mobile surfaces with explicit state semantics.
5. Run backend/frontend validation gates and update docs/changelog evidence.

Rollback:

- Revert to prior composer/session payload wiring while retaining current backend contracts.
- Keep recommendation chips optional so main copilot response path remains functional if chip generation is rolled back.

## Open Questions

- Resolved on 2026-04-05 during `/change-ready` continuation:
  - Keep `dca_2x_v1` as the only strategy profile in this change; defer additional profiles to a follow-up governed-profile change.
  - Keep DCA controls session-local in this change; defer URL/state snapshot persistence to a follow-up workspace-state change.
- Resolved on 2026-04-17 during SOT refactor:
  - Keep this change read-only and deterministic; defer persistent personal-chat memory and advanced calculator/tooling packs to the post-dashboard personal assistant change.
