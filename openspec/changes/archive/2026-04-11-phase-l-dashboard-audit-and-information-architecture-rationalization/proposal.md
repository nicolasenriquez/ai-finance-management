## Why

The current dashboard experience is functionally rich but visually and structurally overloaded for fast decision-making. Route-level composition shows high module density (`Risk` with 7 chart panels and `Quant/Reports` with 8), repeated insight patterns, and heavy shell chrome that competes with core analytical content.

## What Changes

- Add a formal frontend dashboard-audit workflow that inventories every widget and classifies it as `KEEP`, `MERGE`, `MOVE`, or `REMOVE` using business-question and decision-support criteria.
- Add heuristic UX and data-visualization review contracts (state clarity, redundancy, hierarchy, chart suitability, color semantics, discoverability) as implementation gates for dashboard refactors.
- Enforce route-level information-architecture budgets so each analytical route has one dominant first-viewport job and bounded primary module count before progressive disclosure.
- Rebalance workspace shell density (header/trust/pulse/navigation chrome) so the shell supports orientation without dominating first-viewport analytical attention.
- Align frontend dashboard structure to four monitoring lenses (`Overview`, `Holdings`, `Performance`, `Cash/Transactions`) while preserving current backend contracts and compatibility with existing route paths during migration.
- Require textual wireframe and module-priority artifacts for each affected route before implementation tasks are marked complete.

## Capabilities

### New Capabilities
- `frontend-dashboard-widget-governance`: widget-level audit and classification contract for dashboard simplification decisions and traceability.

### Modified Capabilities
- `frontend-analytics-workspace`: route composition and module-priority requirements are tightened to reduce redundancy and enforce progressive disclosure.
- `frontend-workspace-shell-navigation`: shell behavior is updated to support context-preserving but lower-noise chrome density by route mode.
- `frontend-kpi-governance`: governance expands from KPI-only to dashboard decision semantics, including question ownership and benchmark-context requirements.

## Impact

- Frontend pages and layout primitives under `frontend/src/pages/` and `frontend/src/components/workspace-layout/`.
- Frontend workspace governance utilities under `frontend/src/features/portfolio-workspace/`.
- UX governance docs and changelog evidence (`docs/guides/`, `docs/product/`, `CHANGELOG.md`).
- Tests: fail-first and regression coverage for route composition, shell density behavior, and widget audit classifications.
- No backend endpoint or analytics-formula changes are required in this change.
