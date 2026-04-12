## Context

`phase-j` improved workspace shell consistency and copilot access, but route payload presentation has continued to grow in-place. Current route composition shows high visual density and repeated analytical patterns:

- `PortfolioRiskPage.tsx`: 7 `WorkspaceChartPanel` modules plus additional control/state surfaces.
- `PortfolioReportsPage.tsx`: 8 `WorkspaceChartPanel` modules plus large control clusters and dense diagnostics tables.
- `PortfolioWorkspaceLayout.tsx`: persistent shell includes command palette tools, market pulse, and trust context before route content, increasing first-viewport competition.

The requested improvement direction is not a styling-only pass; it is an information-architecture rationalization with explicit audit criteria and elimination of redundant widgets.

Constraints:

- Keep existing backend contracts and endpoint semantics.
- Keep typed frontend contracts and fail-fast route-state behavior.
- Avoid broad route-path breakage during the first migration slice.
- Preserve advanced analytical depth, but move it behind progressive disclosure.

## Goals / Non-Goals

**Goals:**

- Establish a deterministic widget-audit framework for dashboard modules (`KEEP`, `MERGE`, `MOVE`, `REMOVE`).
- Enforce one dominant first-viewport question per route and bounded primary-module budgets.
- Reduce shell chrome competition while preserving navigation and trust context.
- Align dashboard navigation and module grouping with four monitoring lenses: `Overview`, `Holdings`, `Performance`, and `Cash/Transactions`.
- Produce implementation-ready wireframe and governance artifacts before heavy UI refactors.

**Non-Goals:**

- Rewriting backend analytics formulas or adding new analytics endpoints.
- Replacing `Recharts` in this change.
- Removing advanced diagnostics from the product; the goal is relocation and progressive disclosure, not feature deletion.
- Rebuilding copilot architecture in this slice.

## Decisions

### Decision: Add a mandatory widget-audit registry before route refactors

Each dashboard widget will be captured in one registry row with: route, widget type, question answered, decision enabled, source contract, overlap flags, severity, and action (`KEEP/MERGE/MOVE/REMOVE`).

Rationale:

- Prevents subjective “visual polish only” churn.
- Creates auditable rationale for removals and moves.
- Enables deterministic implementation ordering.

Alternatives considered:

- Refactor pages directly without audit registry: rejected due high regression risk and low traceability.

### Decision: Enforce route-level module budgets and tiered disclosure

Routes will adopt a bounded tier model:

- one `Primary` job section per route (mandatory)
- up to 5–7 primary modules in first scrollable surface
- secondary/advanced modules moved behind explicit section boundaries or route transitions

Rationale:

- Improves 5-second scanability and executive comprehension.
- Reduces “many equal-priority panels” anti-pattern.

Alternatives considered:

- Keep current module volume and rely on spacing tweaks: rejected because it does not address cognitive overload.

### Decision: Apply four-lens IA mapping without immediate route-path breakage

The UI will map existing routes to four operational lenses during migration:

- `Overview`: primarily `/portfolio/home`
- `Holdings`: hierarchy + lot detail + holdings-focused views
- `Performance`: `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/reports` interpretation flow
- `Cash/Transactions`: `/portfolio/transactions` plus dividend/cashflow context

Rationale:

- Aligns user mental model with business questions.
- Preserves route compatibility while enabling gradual IA reshaping.

Alternatives considered:

- Immediate hard route rename/restructure: rejected for first slice due migration and deep-link risk.

### Decision: Introduce shell density modes by route context

`PortfolioWorkspaceLayout` will support density modes so route owners can reduce non-critical chrome in high-density analytical contexts.

Rationale:

- Existing shell elements are useful but can dominate first viewport when combined.
- Route-aware shell density keeps orientation while reducing noise.

Alternatives considered:

- One fixed shell density for all routes: rejected because route complexity is not uniform.

### Decision: Use heuristic and visualization severity gates as acceptance criteria

Refactors require explicit severity review against UX heuristics and visualization fit checks (redundancy, chart appropriateness, color semantics, discoverability, navigation clarity).

Rationale:

- Keeps decisions grounded in quality criteria instead of taste.
- Matches requested audit rigor for professionalization.

Alternatives considered:

- “Looks better” acceptance only: rejected as non-repeatable and non-auditable.

## Risks / Trade-offs

- [Over-pruning removes useful analytical depth] -> Preserve advanced modules via secondary sections and route-level drill-down.
- [Migration confusion due IA relabeling] -> Keep path compatibility initially and provide explicit lens labels + cross-route breadcrumbs.
- [Test churn from composition changes] -> Add fail-first composition tests and incremental route-by-route rollout.
- [Governance docs drift from implementation] -> Require changelog + governance artifact updates in the same task group as UI changes.

## Migration Plan

1. Freeze widget inventory and severity audit artifacts for all primary routes.
2. Add fail-first route-composition tests (primary-job dominance, module budget, shell-density behavior).
3. Implement shared shell-density controls and route-lens labels.
4. Apply `KEEP/MERGE/MOVE/REMOVE` actions route by route (Home, Analytics, Risk, Reports, Transactions).
5. Validate accessibility, responsiveness, and deterministic state semantics after each route slice.
6. Update governance docs and changelog with audit evidence and final module decisions.

Rollback:

- Preserve prior route components behind feature flags or reversible composition boundaries.
- Revert route-level IA changes independently if one route fails validation gates.

## Open Questions

- None.
