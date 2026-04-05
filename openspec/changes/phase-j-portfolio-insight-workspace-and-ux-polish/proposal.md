## Why

The portfolio workspace is functionally solid but still feels fragmented, visually conservative, and too route-by-route for the next phase of ML, CAPM, and forecasting insight. Before we add more analytical depth, we need a tighter UX shell that makes high-value finance signals easier to find, compare, and trust across desktop and mobile.

## What Changes

- Add a persistent portfolio insight workspace shell with stable navigation, global command palette, scoped quick-jump behavior, and always-available entry points into portfolio analysis surfaces.
- Recompose Home, Analytics, Risk, Quant/Reports, and Copilot around clearer route jobs, denser analytical layouts, and a `Core 10` metric layer before advanced diagnostics.
- Add personal-finance-specific interpretation surfaces for allocation drift, dividend income, goal progress, forecast confidence, and freshness/trust context so the workspace better supports real portfolio monitoring instead of generic market dashboards.
- Add a shared UI state and utility-copy system for `ready`, `loading`, `stale`, `unavailable`, `blocked`, and `error` so trust semantics remain consistent across routes.
- Upgrade frontend visual direction with a restrained, premium, non-card-mosaic layout system: stronger typography, tighter spacing rhythm, calmer chrome, purposeful motion, and route-consistent explainability affordances.
- Extend the copilot frontend so it can be launched persistently from the workspace shell while preserving evidence, limitations, and read-only guardrails.
- Implement a right-side copilot panel pattern on desktop with explicit collapse/expand controls, plus full-screen mobile behavior and seamless continuity between modes.
- Add copilot suggestion chips that propose context-aware follow-up questions (ChatGPT-style recommendation bubbles) while preserving factual/non-advice boundaries.
- Add composer-level attachment references to previously ingested documents (via `document_id` chips), including visible attachment state and removal controls before submit.
- Keep existing backend contracts, `Recharts`, and fail-fast semantics; explicitly treat OpenStock and impeccable as inspiration sources for interaction patterns and visual discipline rather than code to copy.

## Capabilities

### New Capabilities
- `frontend-workspace-shell-navigation`: Persistent workspace shell, command palette, scoped quick navigation, and cross-route analytical context preservation.

### Modified Capabilities
- `frontend-analytics-workspace`: Rework route information architecture, first-viewport composition, core-versus-advanced metric hierarchy, and personal-finance insight presentation.
- `frontend-ai-copilot-workspace`: Add persistent workspace access, docked-or-expanded interaction patterns, and tighter integration with workspace context while keeping explicit safety boundaries.
- `frontend-kpi-governance`: Expand KPI governance to cover `Core 10` prioritization, personal-finance relevance, route ownership, and explainability requirements for newly promoted metrics.

## Impact

- Frontend: shared workspace shell, navigation primitives, palette/search flow, route layout refactors, and updated page-level composition across `frontend/src/`.
- Contracts: no new backend analytics math is required in this phase, but frontend route behavior and capability contracts change materially.
- Copilot UX contracts: consume backend prompt suggestions and document-reference attachments introduced in `phase-i` without introducing raw-file upload behavior in chat routes.
- UX/design system: new layout rules, typography/motion tokens, state semantics, and accessibility/performance acceptance criteria for analytical surfaces.
- Design implementation process: apply the local `emil-design-eng` skill at `.codex/skills/emil-design-eng/SKILL.md` as a required UI polish rubric for interaction and motion decisions.
- Delivery sequencing: this phase should follow `phase-i` contract stabilization, but it can begin design and shell groundwork before all ML endpoints are implemented.
- Compliance/licensing: public repos such as OpenStock and impeccable are reference inputs for product patterns and design heuristics only; no direct code adoption is assumed by this proposal.
