## Why

`phase-l` rationalized information architecture and reduced dashboard overload, but the workspace still reads more like an internal analytics tool than a professional SaaS product. The next step is to codify a visual system, route composition grammar, and data-visualization rules that make the dashboard feel executive, trustworthy, and decision-ready without undoing the IA gains.

## What Changes

- Add a formal frontend dashboard visual system that defines panel hierarchy, lens-based theming, typography roles, state treatment, and layout rhythm for professional SaaS presentation.
- Redefine primary dashboard routes around an `Executive Operator Workspace` model so each route has one dominant job, one hero insight, and supporting modules ordered as overview, drill-down, and evidence.
- Tighten workspace shell behavior so navigation, freshness, provenance, and global actions remain persistent but no longer compete visually with the route's dominant analytical content.
- Extend KPI and chart governance so promoted insights must declare decision intent, benchmark or target framing, chart-fit rationale, and accessible data-visualization semantics.
- Preserve existing backend contracts, route compatibility, and current typed frontend payload shapes while changing the dashboard's visual and compositional requirements.

## Capabilities

### New Capabilities
- `frontend-dashboard-visual-system`: defines the professional SaaS dashboard visual language, panel hierarchy, typography roles, lens tokens, and lifecycle-state treatment.

### Modified Capabilities
- `frontend-analytics-workspace`: route-level dashboard composition changes to enforce the executive-operator first viewport, route archetypes, and chart sequencing rules.
- `frontend-workspace-shell-navigation`: shell requirements change to support route-aware density, contextual trust rails, and lens-forward orientation without heavy chrome.
- `frontend-kpi-governance`: KPI governance expands to include decision framing, benchmark/target semantics, and chart selection rationale for dashboard surfaces.

## Impact

- Frontend workspace pages and shared layout primitives under `frontend/src/pages/` and `frontend/src/components/workspace-layout/`.
- Dashboard visualization and panel primitives under `frontend/src/components/charts/` and adjacent design tokens in `frontend/src/app/styles.css`.
- Workspace governance utilities and supporting docs under `frontend/src/features/portfolio-workspace/`, `docs/guides/`, and `docs/product/`.
- OpenSpec artifacts, route-composition tests, and UI validation coverage for dashboard structure, shell density, and chart semantics.
