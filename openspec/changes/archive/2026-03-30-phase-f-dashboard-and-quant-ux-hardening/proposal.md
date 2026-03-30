## Why

Phase F is now explicitly documented in the product roadmap, but the repository does not yet have an implementation-ready OpenSpec change that converts that scope into executable requirements and tasks. The current workspace still carries chart duplication, spacing inconsistency, and Quant report UX placement friction that can degrade analyst workflow quality.

## What Changes

- Define analyst-owned KPI taxonomy and route placement requirements for Home, Analytics, Risk, and Quant/Reports surfaces.
- Standardize dashboard chart composition contracts across workspace routes (container sizing, spacing tokens, shared module structure).
- Relocate Quant report generation/retrieval UX from Home into a dedicated analytical context while preserving explicit lifecycle and failure states.
- Tighten route-level information architecture and label semantics to keep preview vs interpretation boundaries deterministic.
- Add fail-first frontend/backend tests for the promoted Quant/Reports route flow, chart composition determinism, and KPI placement rendering contracts.
- Update product/guides/changelog documentation to capture Phase F contracts, deferred items, and validation evidence.

## Capabilities

### New Capabilities
- `frontend-kpi-governance`: Define and enforce analyst-owned KPI catalog and route-level KPI placement contracts for portfolio workspace surfaces.

### Modified Capabilities
- `frontend-analytics-workspace`: Refine route/module information architecture, chart composition standards, and dedicated Quant/Reports workflow placement.
- `frontend-release-readiness`: Extend release-readiness gates to include chart consistency and dedicated Quant/Reports UX validation expectations.
- `portfolio-analytics`: Adjust workspace-facing API contract expectations required by the promoted Quant/Reports UX and KPI route boundaries.

## Impact

- Affected frontend areas:
  - `frontend/src/pages/portfolio-home-page/`
  - `frontend/src/pages/portfolio-analytics-page/`
  - `frontend/src/pages/portfolio-risk-page/`
  - `frontend/src/features/portfolio-workspace/`
  - `frontend/src/components/charts/`
- Affected backend/API areas:
  - `app/portfolio_analytics/routes.py`
  - `app/portfolio_analytics/schemas.py`
  - `app/portfolio_analytics/service.py`
  - `app/portfolio_analytics/tests/`
- Affected docs/OpenSpec artifacts:
  - `docs/product/frontend-ux-analytics-expansion-roadmap.md`
  - `docs/guides/frontend-api-and-ux-guide.md`
  - `CHANGELOG.md`
  - `openspec/specs/frontend-analytics-workspace/spec.md`
  - `openspec/specs/frontend-release-readiness/spec.md`
  - `openspec/specs/portfolio-analytics/spec.md`
- Dependency and governance considerations:
  - Preserve fail-fast semantics and explicit section-level errors for optional quant/report modules.
  - Keep strict typing and deterministic route contracts across backend and frontend clients.
