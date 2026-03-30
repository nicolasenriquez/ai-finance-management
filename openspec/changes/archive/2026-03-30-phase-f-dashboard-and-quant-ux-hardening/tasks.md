## 1. Investigation and KPI Contract Lock

- [x] 1.1 Audit current Home/Analytics/Risk chart modules for duplication, spacing drift, and report-action coupling points.
  Notes:
  - Record exact component-level duplication findings and target consolidation paths before code changes.
  - Audit evidence and consolidation targets are locked in `design.md` under `Current-State Audit (Task 1.1)`.
  - Fixed-width `BarChart` usage (`PortfolioContributionChart`, `PortfolioRiskChart`) versus responsive trend chart behavior is confirmed as the primary spacing/sizing drift source for Phase F.
- [x] 1.2 Define the analyst-owned KPI catalog and route placement matrix (`Home`, `Analytics`, `Risk`, `Quant/Reports`) in docs/change artifacts.
  Notes:
  - Capture KPI name, interpretation narrative, formula notes, and single route owner for each promoted KPI.
  - Named owner role (`Portfolio Analytics Analyst`) and route-scoped KPI placement matrix are locked in `design.md` under `Analyst-Owned KPI Catalog (Task 1.2)`.
- [x] 1.3 Confirm scope boundaries for dedicated `Quant/Reports` workflow and route entry semantics with existing workspace navigation contracts.
  Notes:
  - Keep deterministic route behavior and avoid introducing hidden redirects from existing deep links.
  - Dedicated route contract (`/portfolio/reports`) plus entry semantics and deep-link boundaries are locked in `design.md` under `Quant/Reports Scope and Route Entry Contract (Task 1.3)`.
- [x] 1.4 Lock a senior-analyst visual storytelling contract that defines chart-selection guardrails and anti-patterns for workspace analytics surfaces.
  Notes:
  - Include explicit conventions for comparison/trend/part-to-whole/relationship visuals and accessibility constraints for complex charts.
  - Visual-storytelling guardrails are locked in `design.md` under `Senior Analyst Visual Storytelling Contract (Task 1.4)`.
- [x] 1.5 Define route-level storytelling blueprints (`Home`, `Analytics`, `Risk`, `Quant/Reports`) with one primary analytical question and decision intent per route.
  Notes:
  - Route narratives must prioritize decision flow before detail density.
  - Route storytelling blueprint is locked in `design.md` under `Route Storytelling Blueprint (Task 1.5)`.
- [x] 1.6 Extend KPI governance with KPI-to-visual ownership matrix and explicit visual anti-pattern controls.
  Notes:
  - Each KPI must map to one primary visual, one optional secondary visual, and one guardrail rule.
  - KPI visual ownership matrix is locked in `design.md` under `KPI-To-Visual Matrix (Task 1.6)`.
- [x] 1.7 Document analyst-approved derived financial indicator plan (pandas/QuantStats) with compute-layer and contract-impact guidance.
  Notes:
  - Include at least daily return, cumulative return, drawdown path, rolling volatility/beta, and monthly returns heatmap planning.
  - Derived indicator planning is locked in `design.md` under `Derived Financial Indicator Plan (Task 1.7)`.
- [x] 1.8 Lock a KPI explainability contract that requires definition, relevance, interpretation, comparison context, and current-context notes for promoted metrics.
  Notes:
  - Ground this contract in external KPI guidance that emphasizes business relevance, trend/comparison context, and metric-set coherence.
  - KPI explainability contract is locked in `design.md` under `KPI Explainability Contract (Task 1.8)`.
- [x] 1.9 Lock an action-placement and false-affordance contract for chart tooltips and analytical actions.
  Notes:
  - Hover tooltips may not be the only place where route-changing or export actions exist.
  - False-affordance rules are locked in `design.md` under `Action Placement and False-Affordance Contract (Task 1.9)`.

## 2. Fail-First Test Baseline

- [x] 2.1 Add fail-first frontend tests that reproduce current chart duplication/spacing inconsistencies across workspace routes.
  Notes:
  - Prefer route-level tests tied to shared chart primitives so regressions fail deterministically.
- [x] 2.2 Add fail-first frontend tests that reproduce Home-coupled report workflow behavior expected to move to dedicated `Quant/Reports` surface.
  Notes:
  - Assert explicit loading/error/unavailable/ready states and keyboard-triggered interactions.
- [x] 2.3 Add fail-first backend/API contract tests for route-agnostic Quant report generation/retrieval workflows and explicit lifecycle metadata.
  Notes:
  - Verify requests do not require Home-specific context fields and reject implicit defaults.
- [x] 2.4 Add fail-first frontend tests proving promoted metrics expose explainability affordances and no false-action tooltip controls remain.
  Notes:
  - Assert that important metrics render accessible help affordances and that transient chart tooltips do not expose dead buttons.

## 3. Backend and Contract Alignment

- [x] 3.1 Update portfolio analytics schemas/contracts to expose deterministic scope and lifecycle metadata needed by promoted Quant/Reports UX.
  Notes:
  - Quant-report request payload now forbids extra/untyped fields, and response contract now exposes explicit `lifecycle_status`.
- [x] 3.2 Refactor relevant report service/route logic to remain route-agnostic and fail explicitly for invalid scope or unavailable artifacts.
  Notes:
  - Route contract remains path-agnostic (`/api/portfolio/quant-reports`), while invalid scope/extra fields and unavailable artifacts remain explicit 4xx failures.
- [x] 3.3 Update backend tests for promoted workflow contracts, including invalid-state failures and read-only side-effect boundaries.
  Notes:
  - Backend tests now cover lifecycle metadata, extra-field rejection, invalid scope combinations, unavailable artifact retrieval, and read-only side-effect boundaries.

## 4. Frontend IA and Chart Composition Implementation

- [x] 4.1 Implement dedicated `Quant/Reports` workspace surface (or promoted equivalent) and wire navigation from existing workspace layout.
  Notes:
  - Keep Home as executive snapshot route; report generation entry points should direct users to dedicated analytical context.
- [x] 4.2 Refactor chart modules to use one shared composition contract (container sizing, spacing tokens, shared header semantics) across Home/Analytics/Risk.
- [x] 4.3 Remove duplicated route-local chart wrappers and align module placement with KPI ownership matrix.
- [x] 4.4 Integrate explicit report workflow states and accessibility labeling in promoted Quant/Reports UI controls and previews.
- [x] 4.5 Extend frontend tests for route navigation determinism, chart composition consistency, and report workflow lifecycle handling.
- [x] 4.6 Implement analyst-approved visual modules and guardrails where data contracts already support deterministic rendering.
  Notes:
  - Prioritize: Home period-change waterfall, Analytics contribution waterfall, and one calendar-heatmap style module with explicit precision caveat messaging.
  - Enforce anti-pattern controls (for example, no mixed-unit single-axis risk charting; no high-cardinality pie/donut usage).
- [x] 4.7 Implement accessibility metadata for complex charts with short and long descriptions aligned to route storytelling narratives.
  Notes:
  - Complex chart modules must expose concise summary text plus detailed long-form insight/caveat copy.
  - Keyboard and screen-reader behavior must remain deterministic across route modules.
- [x] 4.8 Implement a shared metric-explainability affordance (`i`/info popover or equivalent) for promoted KPIs and chart metrics.
  Notes:
  - The component must support definition, why-it-matters, interpretation, formula/basis, caveats, and current-context note.
  - Prioritize `Home` KPIs, trend tooltip metrics, risk estimators, and quant scorecards.
- [x] 4.9 Remove false-affordance controls from transient tooltips and relocate valid actions into persistent, testable surfaces.
  Notes:
  - `Analyze Risk` should deep-link deterministically into `/portfolio/risk` only from a stable action surface.
  - `Export CSV` should only appear after an explicit deterministic export contract is implemented.

## 5. Documentation and Governance Updates

- [x] 5.1 Update product and frontend guide docs with finalized KPI matrix, route IA, and Quant/Reports workflow boundaries.
- [x] 5.2 Update OpenSpec deltas (if implementation-driven refinements emerge) so specs remain implementation-accurate before closeout.
- [x] 5.3 Add `CHANGELOG.md` entry summarizing Phase F behavior changes, files touched, and validation evidence.
- [x] 5.4 Update product/guide/standard docs with finalized visual-governance rules, route storytelling contract, and derived-metrics scope boundaries.
  Notes:
  - Align `docs/product/frontend-ux-analytics-expansion-roadmap.md`, `docs/guides/frontend-api-and-ux-guide.md`, and `docs/standards/quantstats-standard.md` with implemented behavior.
  - Preserve explicit distinction between currently shipped visuals and approved follow-up derived indicator modules.
- [x] 5.5 Update documentation with KPI definitions, why-it-matters copy rules, and tooltip/action placement standards for analytical surfaces.
  Notes:
  - Document naming guidance for ambiguous shorthand such as `PnL`, `Trendline`, and normalized benchmark labels.
  - Record the rule that non-functional analytical actions must not be rendered.

## 6. Validation and Closeout

- [x] 6.1 Run backend quality gates and targeted portfolio analytics tests for report-contract changes.
- [x] 6.2 Run frontend gates (`lint`, `test`, `build`) including updated workspace route and report-flow test suites.
- [x] 6.3 Run OpenSpec validation for the Phase F change and all specs, then record pass/fail evidence in changelog and artifacts.
