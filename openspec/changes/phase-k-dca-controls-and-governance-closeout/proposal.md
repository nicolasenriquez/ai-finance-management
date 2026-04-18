## Why

The current copilot flow still hardcodes DCA policy inputs in frontend session code, which makes opportunity-scan behavior less transparent and harder to tune safely.

At the same time, the existing copilot logic does not yet treat a full DCA investing guideline as one canonical source of truth (SOT) for assessments. This creates drift risk between:

- deterministic scanner outputs
- AI narration style
- recommendation prompts presented in the workspace

With the compact dashboard change now in progress, this change must leave a governed DCA SOT contract that can power the upcoming personal chat assistant without inventing new policy semantics later.

## What Changes

- Preserve explicit DCA opportunity controls (`opportunity_strategy_profile`, `double_down_threshold_pct`, `double_down_multiplier`) from UI to backend typed contracts.
- Remove hidden frontend fallback behavior for DCA controls so submitted values are user-visible, validated, and deterministic.
- Preserve and harden deterministic DCA classification semantics, including strict gating that prevents `double_down_candidate` when full 52-week history is not evaluable.
- Add a DCA SOT assessment envelope so recommendations consistently evaluate:
  - plan discipline (baseline cadence)
  - dip qualification (threshold and history eligibility)
  - fundamentals proxy state and reason codes
  - capital/risk guardrail caveats (overconcentration, insufficient context)
  - next-check guidance (review cadence and follow-up prompts)
- Formalize operation-aware recommendation bubbles for both general chat and DCA opportunity-scan workflows, with portfolio-governance language rather than generic prompts.
- Freeze post-dashboard assistant UX posture for this slice as read-only, transparency-first:
  - docked lateral panel on desktop
  - expanded copilot route for deep review
  - event-aware chat rendering (`start`, token streaming intent, `tool_call`, `end`) for deterministic trust inspection
- Close governance and validation for this slice with targeted backend/frontend test coverage and updated delivery docs.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `portfolio-ai-copilot`: Add explicit DCA-control contract behavior, deterministic history-gating semantics, and SOT-aligned DCA assessment framing for opportunity classification/narration.
- `frontend-ai-copilot-workspace`: Add visible DCA controls in composer/request flow, operation-aware portfolio recommendation bubbles, and transparency-first assistant presentation semantics aligned with post-dashboard personal copilot direction.

## Impact

- Backend: `app/portfolio_ai_copilot/` request validation, deterministic scanner policy wiring, and related tests.
- Frontend: `frontend/src/features/portfolio-copilot/`, `frontend/src/core/api/schemas.ts`, and `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.tsx`.
- Contracts: Copilot request semantics become explicit and user-configurable for DCA scans, with SOT-consistent DCA assessment semantics.
- Governance: docs/changelog validation evidence updated for DCA control-surface, recommendation-bubble behavior, and SOT DCA guidance posture.
