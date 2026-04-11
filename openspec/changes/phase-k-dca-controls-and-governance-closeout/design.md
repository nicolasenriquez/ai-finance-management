## Context

`phase-j` delivered the workspace shell and copilot presentation polish, and `phase-i` delivered AI/ML contract layering. The DCA opportunity flow is functionally available, but key policy controls are still hardcoded in frontend session defaults, which weakens transparency and operator control. At the same time, recommendation bubbles need an explicit quality bar so the UI consistently proposes business and portfolio-governance follow-ups.

Constraints:

- Keep read-only copilot boundaries and non-advice posture unchanged.
- Keep deterministic opportunity ranking formula and bounded request limits.
- Preserve strict typed contracts across Python schemas and frontend Zod schemas.
- Follow fail-first test posture for behavior changes.

## Goals / Non-Goals

**Goals:**

- Make DCA policy inputs explicit and user-visible from composer controls to backend request payload.
- Preserve deterministic and safe classification behavior, including no `double_down_candidate` result when 52-week eligibility cannot be evaluated.
- Upgrade recommendation bubbles into operation-aware, business-grade prompt catalogs for chat and DCA flows.
- Close governance with tests, type gates, and documentation updates.

**Non-Goals:**

- Introducing trade execution, rebalance automation, or financial-advice guarantees.
- Changing the opportunity scoring formula weights.
- Adding persistent memory or vector-store behavior to copilot.

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

### Decision: Enforce operation-aware, portfolio-business recommendation bubbles

Suggestion chips will be curated per operation (`chat` vs `opportunity_scan`) and prioritize allocation, concentration, benchmark context, drawdown governance, and capital-deployment framing.

Rationale:

- Aligns prompt guidance with passive-investor and portfolio-governance outcomes.
- Reduces low-signal or generic question suggestions.

Alternatives considered:

- One generic suggestion pool for all operations: rejected because it dilutes analytical relevance.

## Risks / Trade-offs

- [Higher UI density in composer controls] -> Keep DCA controls conditionally visible for `opportunity_scan` only and preserve compact/mobile ergonomics.
- [Validation mismatch between frontend/backed decimal handling] -> Keep strict schema parity and add fail-first request-shape tests.
- [Suggestion copy regresses into generic phrasing over time] -> Freeze business-grade prompt catalogs in tests and update governance docs with acceptance language.

## Migration Plan

1. Add fail-first tests for DCA control visibility, payload propagation, and 52-week gating behavior.
2. Implement typed contract wiring in backend schemas/service and frontend schemas/session/composer.
3. Add operation-aware recommendation bubble catalogs and deterministic selection behavior.
4. Run backend/frontend validation gates and update docs/changelog evidence.

Rollback:

- Revert to prior composer/session payload wiring while retaining current backend contracts.
- Keep recommendation chips optional so main copilot response path remains functional if chip generation is rolled back.

## Open Questions

- Resolved on 2026-04-05 during `/change-ready` continuation:
  - Keep `dca_2x_v1` as the only strategy profile in this change; defer additional profiles to a follow-up governed-profile change.
  - Keep DCA controls session-local in this change; defer URL/state snapshot persistence to a follow-up workspace-state change.
- None.
