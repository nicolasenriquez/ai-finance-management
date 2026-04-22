## Why

After the compact two-tab dashboard (`archive-v0-and-build-compact-trading-dashboard`) is live and DCA control/governance closeout (`phase-k-dca-controls-and-governance-closeout`) is complete, the next product step is a personal chat assistant that can assess DCA decisions using one canonical DCA investing guideline (SOT).

Current copilot functionality is useful, but still limited for this job:

- DCA guidance is spread across deterministic outputs and free-form narration
- personal guardrails (overinvesting, pause/reduce conditions, review cadence) are not first-class assessment inputs
- the chat UI lacks dedicated calculator/tooling surfaces for DCA planning
- chat lifecycle and tool activity are not fully visible as first-class user-facing events
- conversation continuity for longitudinal DCA reviews is session-fragile

This change formalizes a personal DCA assistant contract so recommendations are evidence-backed, deterministic where possible, and consistently aligned with DCA discipline.

## What Changes

- Introduce a governed DCA SOT rulebook in copilot assessment flow, covering:
  - baseline DCA cadence discipline
  - double-down threshold policy with strict 52-week eligibility
  - fundamentals verification posture (proxy + explicit caveat)
  - concentration and risk-control framing
  - pause/reduce conditions and next-check cadence
- Extend copilot operations with one personal-assessment mode (`dca_assessment`) that uses the DCA SOT envelope as response structure.
- Add deterministic DCA calculator tools for planning and comparison, including:
  - baseline vs 2x DCA scenario comparison
  - projected average-cost-basis impact
  - concentration delta by symbol/sector after planned adds
  - threshold-monitor checks for current holdings
- Add typed personal policy context inputs (bounded, optional, explicit insufficiency when absent) for budget/risk constraints.
- Add deterministic context cards to every DCA assessment request/response cycle:
  - top gainers and losers snapshot
  - held-symbol concentration deltas
  - bounded news-context summary for symbols relevant to recommendations
- Add assistant workspace UX for practical daily use:
  - docked lateral panel + expanded full surface
  - chat + calculators + policy summary modules
  - event-aware timeline for response lifecycle and tool usage transparency (`start`, `token`, `tool_call`, `end`, `error`)
- Add bounded conversation persistence and replay for personal DCA review continuity:
  - persisted chat session metadata and message history
  - deterministic evidence linkage for historical recommendations
- Add assistant observability standards (traceability for model runs, tool calls, latency, token usage, and error states) for governance/debugging.
- Keep read-only boundaries, non-execution constraints, and non-advice messaging unchanged.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `portfolio-ai-copilot`: add DCA-SOT personal assessment mode, deterministic DCA calculator tooling, typed policy-context semantics, context-card synthesis, event-stream contract, and bounded conversation persistence semantics.
- `frontend-ai-copilot-workspace`: add personal assistant interaction model with DCA calculator surfaces, transparent tool-event lifecycle presentation, persisted-session continuity, and context-card rendering.

## Impact

- Backend: `app/portfolio_ai_copilot/` schemas, service orchestration, deterministic calculator modules, and tests.
- Frontend: `frontend/src/features/portfolio-copilot/`, `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.tsx`, and associated typed API schema wiring.
- Contracts: request/response payloads expand to support `dca_assessment`, policy context, calculator outputs, tool-event stream metadata, and persisted-session references.
- Governance: OpenSpec specs, guide docs, and changelog evidence updated for SOT DCA assistant behavior, event-trace transparency, and observability baselines.
