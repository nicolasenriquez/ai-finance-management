## Context

`phase-l-dashboard-audit-and-information-architecture-rationalization` established route budgets, progressive disclosure, and a four-lens map. That change improved cognitive load, but it did not fully define the visual grammar that makes a dashboard feel like a premium SaaS workspace rather than a collection of functional modules.

The current frontend already has reusable workspace primitives, but they still allow:

- multiple modules with similar visual weight in the first viewport
- shell chrome that competes with route content in dense analytical screens
- route compositions that are structurally improved yet still stylistically uneven
- charts that answer the right question in principle but do not always communicate benchmark context, evidence depth, or accessibility semantics consistently

The requested proposal is therefore not another IA audit. It is a professionalization pass that turns `phase-l` findings into a stable dashboard design system and route contract.

Constraints:

- Keep current backend contracts and typed frontend payloads.
- Preserve existing route compatibility during migration.
- Avoid speculative re-platforming of chart libraries or data APIs.
- Keep advanced analytics available through progressive disclosure instead of deleting depth.
- Respect the existing dirty worktree and active `phase-k` change by containing this work to a new OpenSpec change only.

## Goals / Non-Goals

**Goals:**

- Define a professional dashboard visual system with explicit hierarchy for `hero`, `standard`, and `utility` panels.
- Recompose dashboard routes around one dominant first-viewport job using the `Overview -> drill-down -> evidence` pattern from the dashboard skill guidance.
- Make shell chrome route-aware so orientation remains persistent while first-viewport analytical clarity improves.
- Codify benchmark, target, and chart-fit requirements so KPI and visualization choices remain auditable and non-decorative.
- Produce implementation-ready OpenSpec artifacts that can drive a route-by-route UI redesign without backend churn.

**Non-Goals:**

- Rebuilding analytics endpoints, formulas, or storage contracts.
- Replacing `Recharts` in this phase.
- Introducing a brand-new navigation taxonomy beyond the lens and route adjustments already aligned in `phase-l`.
- Delivering production UI changes in this planning step.

## Decisions

### Decision: Introduce a dedicated dashboard visual-system capability

The change adds a new capability, `frontend-dashboard-visual-system`, instead of scattering visual rules across page-level specs.

Rationale:

- The repo currently has IA and KPI governance, but no stable contract for visual hierarchy, lens theming, typography roles, or lifecycle-state presentation.
- A dedicated capability makes the redesign testable and prevents a purely aesthetic, non-repeatable implementation.

Alternatives considered:

- Fold all visual requirements into `frontend-analytics-workspace`: rejected because it would mix route behavior with reusable visual-system primitives.

### Decision: Adopt an `Executive Operator Workspace` composition model

Each primary route will follow a first-viewport template:

- lens label plus freshness/provenance support
- one primary job panel
- one hero insight
- two to four supporting modules
- advanced diagnostics behind explicit disclosure

Rationale:

- This directly extends `phase-l`'s one-dominant-job rule into a stronger compositional contract.
- It matches the `building-dashboards` skill principle that dashboards must move from overview to drill-down to evidence and that one panel should answer one question.

Alternatives considered:

- Keep current route composition and only restyle cards: rejected because visual polish without composition discipline will preserve equal-priority clutter.

### Decision: Make shell density route-aware and subordinate to analytical focus

The shell will remain persistent, but density modes become a first-class requirement. Freshness, provenance, and route context shift into a compact support rail instead of dominating the same visual layer as the route hero.

Rationale:

- Existing shell persistence is valuable, but dense routes need lower chrome competition.
- This preserves navigation consistency without sacrificing first-viewport analytical clarity.

Alternatives considered:

- Remove shell utilities entirely on dense routes: rejected because it weakens orientation and shared context.

### Decision: Encode chart semantics as part of KPI governance, not visual afterthought

Promoted dashboard insights must specify:

- decision enabled
- target or benchmark framing
- primary chart type and why it fits the data relationship
- fallback table or textual evidence path when accessibility or interpretation requires it

Rationale:

- The `data-visualization` skill emphasizes that chart choice must follow data relationship, not aesthetics.
- The dashboard skill emphasizes that each panel must answer a decisionable question.
- Folding this into governance prevents decorative or redundant charts from reappearing later.

Alternatives considered:

- Leave chart decisions to implementation review only: rejected because that creates inconsistent route outcomes and weak archiveability.

### Decision: Use a restrained premium fintech aesthetic instead of novelty styling

The recommended visual direction is institutional and calm:

- deep graphite or petroleum surfaces instead of pure black
- restrained blue/neutral base with lens-specific accents
- status colors reserved for semantic meaning
- serious sans typography for narrative UI, tabular numeric treatment for metrics

Rationale:

- `ui-ux-pro-max` recommendations for executive and financial dashboards favor high signal, strong typographic discipline, and limited accent use.
- This aesthetic supports trust and operational focus better than heavily stylized or trend-driven approaches.

Alternatives considered:

- Strong glassmorphism or novelty gradients: rejected because they undermine clarity and aging stability for a dense analytical product.

## Risks / Trade-offs

- [Visual-system scope drifts into endless polish work] -> Bind the redesign to reusable primitives, route templates, and acceptance checks instead of subjective iteration loops.
- [Route composition loses analytical depth] -> Keep advanced diagnostics behind explicit disclosure and maintain evidence paths from hero insight to raw tables.
- [Lens theming becomes ornamental rather than functional] -> Require semantic use of accent colors for route orientation and state cues, not decorative saturation.
- [Chart-governance rules create implementation friction] -> Limit governance to promoted insights and first-surface visuals; advanced diagnostics can remain simpler if they preserve clarity and accessibility.
- [Dirty worktree and active change create coordination risk] -> Keep this proposal isolated to new OpenSpec artifacts and do not modify application code in this step.

## Migration Plan

1. Freeze the new visual-system contract, route templates, and chart-governance deltas in OpenSpec.
2. Convert shared primitives first: shell density, panel variants, typography roles, and route support rail.
3. Redesign `Overview/Home` as the reference implementation for the new dashboard language.
4. Apply the same system to `Holdings`, `Performance`, and `Cash/Transactions` route families with route-specific module contracts.
5. Update governance artifacts, UX docs, and changelog evidence alongside each route slice.
6. Validate route composition, state semantics, responsiveness, and build/test gates before wider rollout.

Rollback:

- Revert route-level redesign slices independently while keeping the proposal and governance artifacts intact.
- Preserve existing route compatibility and data contracts so visual rollback does not require backend rollback.

## Open Questions

- None.
