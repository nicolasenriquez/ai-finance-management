# Phase L Dashboard IA Implementation Handoff

Date: 2026-04-05
Change: `phase-l-dashboard-audit-and-information-architecture-rationalization`

## Delivered Scope
- Route-aware shell density policy implemented in workspace shell (`expanded`, `balanced`, `compact`).
- Analytics/Risk/Reports first-surface rationalization applied with explicit progressive-disclosure controls.
- Governance contract added for route-level question ownership, decision tags, module budgets, and comparison framing.
- Dashboard audit evidence published in [phase-l-dashboard-audit-and-ia-rationalization.md](./phase-l-dashboard-audit-and-ia-rationalization.md).

## Regression Watchpoints
- Route-level accessibility of advanced modules must remain keyboard reachable via disclosure buttons.
- Future additions to Risk/Reports can silently break first-surface budgets unless governance metadata and tests are updated in lockstep.
- Command palette route hints now include lens framing; copy regressions should preserve destination path semantics.
- Compact shell mode should not remove trust/provenance context on routes that require it.

## Unresolved / Deferred Risks
- Holdings lens remains mapped through grouped summary + lot detail routes and is not yet represented as a dedicated workspace-nav tab in this slice.
- Monthly heatmap remains contract-dependent on time-series availability and can present limited interpretability on sparse instrument scopes.

## Acceptance Evidence
- IA contract tests and route tests: see frontend Vitest run evidence in the validation section of `CHANGELOG.md` (2026-04-05 phase-l entry).
- OpenSpec change + spec validation: `phase-l-dashboard-audit-and-information-architecture-rationalization` status/validate outputs.
- Audit artifacts: widget inventory, severity findings, disposition matrix, and route wireframes in [phase-l-dashboard-audit-and-ia-rationalization.md](./phase-l-dashboard-audit-and-ia-rationalization.md).
