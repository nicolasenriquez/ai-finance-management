## Why

The current copilot flow still hardcodes DCA policy inputs in frontend session code, which makes opportunity-scan behavior less transparent and harder to tune safely. We also need to formalize business-grade recommendation bubbles so prompts stay portfolio-informative and aligned with passive-investor decision workflows.

## What Changes

- Expose DCA opportunity controls (`opportunity_strategy_profile`, `double_down_threshold_pct`, `double_down_multiplier`) as explicit first-class inputs from copilot UI through typed frontend and backend contracts.
- Remove hidden frontend fallback behavior for DCA controls so submitted values are user-visible, validated, and deterministic.
- Preserve and harden deterministic DCA classification semantics, including strict gating that prevents `double_down_candidate` when full 52-week history is not evaluable.
- Formalize operation-aware recommendation bubbles for both general chat and DCA opportunity-scan workflows, with business and portfolio language rather than generic prompts.
- Close governance and validation for this slice with targeted backend/frontend test coverage and updated delivery docs.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `portfolio-ai-copilot`: Add explicit DCA-control contract behavior and deterministic history-gating semantics for opportunity classification.
- `frontend-ai-copilot-workspace`: Add visible DCA controls in composer/request flow and operation-aware portfolio recommendation bubbles.

## Impact

- Backend: `app/portfolio_ai_copilot/` request validation, deterministic scanner policy wiring, and related tests.
- Frontend: `frontend/src/features/portfolio-copilot/`, `frontend/src/core/api/schemas.ts`, and `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.tsx`.
- Contracts: Copilot request semantics become explicit and user-configurable for DCA scans.
- Governance: docs/changelog validation evidence updated for DCA control-surface and recommendation-bubble behavior.
