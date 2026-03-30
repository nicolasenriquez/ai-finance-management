## Context

The portfolio workspace now has functional Home, Analytics, Risk, and Transactions routes, plus Quant report generation/retrieval contracts. However, dashboard composition still shows route-to-route inconsistency (duplicated chart modules, uneven spacing/sizing behavior), and report actions remain semantically coupled to Home despite a roadmap decision to promote report workflows into a dedicated analytical context.

Phase F is a cross-cutting frontend + contract alignment slice. It touches route information architecture, frontend composition primitives, API consumption boundaries for report workflows, and release-readiness evidence gates. The implementation must preserve repository constraints: fail-fast behavior, explicit state rendering, strict typing, deterministic route contracts, and accessibility-first controls.

## Current-State Audit (Task 1.1)

### Chart module duplication and consolidation targets

- Home, Analytics, and Risk pages all implement route-local chart panel wrappers with repeated `section.panel` + `panel__header` + `panel__body` composition around chart modules.
  - Home: `frontend/src/pages/portfolio-home-page/PortfolioHomePage.tsx`
  - Analytics: `frontend/src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx`
  - Risk: `frontend/src/pages/portfolio-risk-page/PortfolioRiskPage.tsx`
- `PortfolioTrendChart` is reused in both Home and Analytics but still receives route-local header wrappers, while the chart component itself also renders a header region (`chart-header`) and summary cards. This creates inconsistent header layering compared with contribution/risk charts.
- Consolidation path:
  - Introduce one shared workspace chart-panel composition primitive for title/subtitle/body scaffolding.
  - Keep chart components focused on chart-specific rendering and controls, not route-local container semantics.

### Spacing and sizing drift evidence

- Trend chart uses responsive container sizing (`ResponsiveContainer` with `width="100%"` and `height={320}`), while contribution and risk charts use fixed-width `BarChart` instances (`width={760}`, `height={280}`).
  - `frontend/src/components/charts/PortfolioTrendChart.tsx`
  - `frontend/src/components/charts/PortfolioContributionChart.tsx`
  - `frontend/src/components/charts/PortfolioRiskChart.tsx`
- Shared styling tokens exist (`.panel__body`, `.chart-surface`), but route-local modules add inconsistent secondary content blocks (`trend-list`, `lot-metrics`, quant report summary/iframe) that produce non-deterministic vertical rhythm between routes.
  - `frontend/src/app/styles.css`
- Consolidation path:
  - Use one shared chart composition contract for container width/height behavior and panel spacing.
  - Move route-specific narrative content to explicit secondary slots so primary chart spacing stays deterministic.

### Report-action coupling points

- Home currently owns full report workflow state and UI controls:
  - Report request/validation/mutation state in `PortfolioHomePage`.
  - Report generation controls and preview rendering in the same route.
- Workspace navigation excludes dedicated report route:
  - Router registers Home/Analytics/Risk/Transactions only.
  - Workspace nav links include no Quant/Reports entry.
- Coupling implication:
  - Quant report generation and retrieval remains semantically Home-owned, which conflicts with Phase F dedicated analytical-surface intent.

## Analyst-Owned KPI Catalog (Task 1.2)

**Named owner role:** Portfolio Analytics Analyst

The KPI catalog below is the locked placement contract for Phase F implementation. Each KPI has one route owner to prevent duplication drift.

| KPI ID | KPI Name | Interpretation Narrative | Formula / Source Notes | Route Owner |
|---|---|---|---|---|
| `market_value_usd` | Market value | Current total value of open positions for executive snapshot. | Sum of `summary.rows[].market_value_usd`. | `Home` |
| `unrealized_gain_usd` | Unrealized gain | Open-position gain/loss versus cost basis. | Sum of `summary.rows[].unrealized_gain_usd`. | `Home` |
| `period_change_usd` | Period change | Snapshot delta across selected period for first-viewport trust context. | `latest(portfolio_value_usd) - first(portfolio_value_usd)` from time-series points. | `Home` |
| `portfolio_total_return_pct` | Portfolio total return | Performance interpretation across selected window. | Relative return from first to latest portfolio point. | `Analytics` |
| `benchmark_spread_pct` | Excess return vs benchmark | Analyst view of portfolio out/under-performance versus available benchmark context. | `portfolio_return - benchmark_return` (S&P 500 / NASDAQ-100 proxy when available). | `Analytics` |
| `top_contribution_pnl` | Top contribution symbols | Primary attribution KPI for symbol-level period impact. | Top absolute rows from contribution endpoint (`contribution_pnl_usd`, `contribution_pct`). | `Analytics` |
| `risk_estimator_value` | Risk estimator metrics | Methodology-aware risk interpretation for selected window. | `risk-estimators` endpoint values + annualization metadata (`window_days`, `return_basis`, `annualization_basis`). | `Risk` |
| `quant_metric_card` | Quant diagnostic metrics | Supplemental quant diagnostics for report interpretation and scope decisions. | Ordered QuantStats metrics (`sharpe`, `sortino`, `calmar`, `volatility`, `max_drawdown`, `alpha`, `beta`, `win_rate`) from quant-metrics payload. | `Quant/Reports` |
| `quant_report_lifecycle` | Report artifact lifecycle | Deterministic report artifact state for generation/retrieval UX. | Report metadata (`report_id`, `scope`, `period`, `benchmark_symbol`, `generated_at`, `expires_at`). | `Quant/Reports` |

## Quant/Reports Scope and Route Entry Contract (Task 1.3)

Dedicated route and ownership contract, confirmed against current router and workspace navigation patterns:

- Add one dedicated workspace route path: `/portfolio/reports` with nav label `Quant/Reports`.
- `Quant/Reports` owns:
  - Quant diagnostic metrics rendering.
  - Quant report generation controls.
  - Report lifecycle state rendering (`loading`, `error`, `unavailable`, `ready`) and HTML preview actions.
- `Home` remains executive snapshot-only:
  - Keep KPI snapshot, trust context, trend preview, and drill-down entry points.
  - Replace full report workflow ownership with explicit navigation into `Quant/Reports`.

Route-entry semantics and deep-link boundaries:

- Preserve existing canonical paths (`/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/transactions`, `/portfolio/:symbol`) and existing root redirects.
- Do not introduce hidden redirects from Home to Quant/Reports.
- Preserve deterministic query behavior by forwarding `period` when users enter `Quant/Reports` from period-scoped routes.
- Keep backend report contracts route-agnostic:
  - Continue using `/api/portfolio/quant-reports` and `/api/portfolio/quant-reports/{report_id}` without Home-origin request flags.

## Senior Analyst Visual Storytelling Contract (Task 1.4)

This contract formalizes how the `Portfolio Analytics Analyst` role chooses visuals and narrative flow for each route.

### External conventions adopted (research baseline: 2026-03-29)

- Use bars/columns as default for categorical comparison; use lines for time trends.
- Use waterfall charts when the user must understand additive positive/negative drivers from one baseline to another.
- Treat pie/donut as constrained visuals only for small category counts and high-level part-to-whole framing.
- Avoid mixed-unit comparisons on a single axis (for example, plotting beta and volatility on one unnormalized Y-axis).
- Prefer pattern-first views (for example, calendar heatmap) for temporal rhythm, and keep precision-first values in adjacent tables/cards.
- Accessibility baseline for complex charts:
  - short alt description + long textual description for trends, values, and caveats.
  - avoid color-only encoding for critical meaning.

### Visual-selection guardrails (route-independent)

| Analysis goal | Preferred visual | Optional alternate | Avoid by default | Rationale |
|---|---|---|---|---|
| Compare magnitudes across categories | Ordered horizontal bar | Lollipop | Pie/donut for ranked comparisons | Position/length comparisons are most reliable. |
| Explain change over time | Line | Area (single-series, with care) | Stacked area for precise component comparison | Line emphasizes trend shape and direction. |
| Explain additive contribution to total delta | Waterfall | Diverging ordered bars | Pie/donut | Waterfall exposes sequential positive/negative drivers. |
| Show part-to-whole with many nodes | Treemap | 100% stacked bar | Pie with many slices | Treemap/stacked bars scale better with category count. |
| Show daily/weekly temporal rhythm | Calendar heatmap | Small multiples lines | Dense table only | Heatmap makes recurrence and seasonality visible quickly. |
| Show relationship between two metrics | Scatter | Bubble (third variable) | Dual-axis line for non-time relations | Scatter is better for correlation/clustering/outliers. |

## Route Storytelling Blueprint (Task 1.5)

Each route must answer one primary analytical question before showing secondary detail.

| Route | Primary question | Primary decision enabled | Narrative sequence | Primary visual modules |
|---|---|---|---|---|
| `Home` | "How is the portfolio doing right now?" | Triage whether to drill into performance, risk, or reporting workflows. | KPI snapshot -> period bridge -> trend context -> route drill-down actions. | KPI cards, period-change waterfall, portfolio vs benchmark line preview. |
| `Analytics` | "What drove the selected-period result?" | Identify top positive/negative contributors and concentration risk. | Total return context -> attribution ranking -> contribution bridge -> pattern context. | Trend line, ordered contribution bars, contribution waterfall, calendar returns heatmap. |
| `Risk` | "What risk profile explains this performance?" | Decide whether risk is acceptable for current return profile and window. | Risk summary -> drawdown behavior -> volatility/beta behavior -> methodology context. | Risk cards, drawdown line, rolling volatility/beta small multiples, return distribution histogram. |
| `Quant/Reports` | "What diagnostic evidence supports the next action?" | Generate/retrieve reports, validate benchmark context, and compare quant diagnostics. | Quant scorecard -> benchmark availability/omission context -> report lifecycle -> preview/full report actions. | Quant metric scorecards, optional monthly returns heatmap, report lifecycle state panel, HTML preview. |

## KPI-To-Visual Matrix (Task 1.6)

This matrix extends KPI ownership with deterministic visual ownership and anti-pattern controls.

| KPI ID | Route owner | Primary visual | Secondary visual | Guardrails | Data status |
|---|---|---|---|---|---|
| `market_value_usd` | `Home` | KPI card | Sector treemap (drill-only) | Never use pie for full symbol universe. | Available from `summary.rows[].market_value_usd`. |
| `unrealized_gain_usd` | `Home` | KPI card with tone | Diverging bars by symbol (top movers) | Keep sign encoding explicit (+/- and color). | Available from `summary.rows[].unrealized_gain_usd`. |
| `period_change_usd` | `Home` | Waterfall (start -> drivers -> end) | Signed delta card | Preserve bridge ordering and signed bars. | Derivable from time-series first/latest values and contribution rows. |
| `portfolio_total_return_pct` | `Analytics` | Normalized line (portfolio + benchmarks) | Slope chart (period endpoints) | Keep common baseline and aligned date index. | Derivable from time-series + benchmark series. |
| `benchmark_spread_pct` | `Analytics` | Spread line (portfolio minus benchmark) | Signed bar by period bucket | Do not hide missing benchmark context; show omission state. | Derivable when benchmark exists. |
| `top_contribution_pnl` | `Analytics` | Ordered horizontal bars | Waterfall contribution bridge | Sort by absolute contribution and preserve sign. | Available from contribution endpoint. |
| `risk_estimator_value` | `Risk` | Metric cards by estimator | Small-multiple lines for rolling estimators | Do not chart mixed units on one shared Y-axis. | Cards available now; rolling series requires derived metrics pipeline. |
| `quant_metric_card` | `Quant/Reports` | Scorecard grid | Grouped table with sparkline column | Keep metric label + formula context visible. | Available from quant metrics endpoint. |
| `quant_report_lifecycle` | `Quant/Reports` | Explicit state panel (`loading/error/unavailable/ready`) | Timeline of report events | Lifecycle is stateful UX, not inferred from missing fields. | Available from report generate/retrieve metadata. |

## Derived Financial Indicator Plan (Task 1.7)

The following indicators are approved for Phase F implementation planning. They are not all required in the first merge, but they are now part of the analyst-approved roadmap.

| Indicator ID | Formula / method | Compute layer | Visual target | Contract impact |
|---|---|---|---|---|
| `daily_return_pct` | `pct_change(portfolio_value)` x `100` | Backend preferred (`pandas`) | Calendar heatmap + distribution histogram | Uses existing time-series inputs; no new source tables. |
| `cumulative_return_pct` | `(1+r).cumprod()-1` | Backend preferred (`pandas`) | Trend line index view | Can be derived from existing points. |
| `drawdown_path_pct` | `value/cummax(value)-1` | Backend preferred (`pandas`/QuantStats parity checks) | Risk drawdown line | Enables richer Risk storytelling than max drawdown card only. |
| `rolling_volatility_21d_63d` | `std(returns)*sqrt(252)` on rolling window | Backend preferred | Risk small multiples | Requires explicit window metadata in payload. |
| `rolling_beta_63d` | `cov(portfolio, benchmark)/var(benchmark)` | Backend preferred | Risk small multiples | Requires benchmark-aligned return series and omission handling. |
| `return_distribution_bins` | Histogram bucketization on returns | Backend preferred | Risk histogram | Keep deterministic bin policy for repeatable visuals. |
| `monthly_return_heatmap` | Monthly pivot of period returns | Quant/Reports backend helper | Quant diagnostics heatmap | Best rendered with supporting table for precision. |

### Computation notes

- `pandas.DataFrame.pct_change` returns fractional change; percent presentation must multiply by `100`.
- QuantStats remains the approved adapter for advanced stats/reports; derived indicators must preserve existing fail-fast semantics and explicit omission metadata for benchmark-relative calculations.

### Analyst recommendation for Phase F implementation order

1. Ship visual governance and route storytelling contracts first (this design section).
2. Deliver `Quant/Reports` route relocation and chart composition standardization.
3. Add one first derived-series module (`drawdown_path_pct` + `daily_return_pct` heatmap) to validate the computation-to-visual pipeline.
4. Expand rolling risk indicators (`rolling_volatility`, `rolling_beta`) after route contracts are stable.

## KPI Explainability Contract (Task 1.8)

External KPI guidance reviewed on 2026-03-29 reinforces five useful principles for this workspace:

- each KPI must be meaningful to the business context rather than chosen generically.
- one KPI is only a point-in-time snapshot unless it is paired with trend/comparison context.
- KPI value increases when compared over time, against a target, or versus a benchmark.
- KPI definitions should explain why a number matters, not just how it is calculated.
- KPI sets should work together as one decision system instead of isolated tiles.

For this portfolio workspace, those principles are adapted into one mandatory explainability schema for analyst-owned metrics.

### Required explainability fields for promoted KPIs

Every KPI or metric exposed as primary analytical context SHALL have:

| Field | Purpose |
|---|---|
| `plain_label` | Human-readable name that avoids unexplained shorthand where possible. |
| `short_definition` | One-sentence explanation of what the metric measures. |
| `why_it_matters` | One-sentence explanation of why this metric is relevant to an analyst decision. |
| `formula_or_basis` | Formula, derivation basis, or source note. |
| `interpretation_rule` | What positive/negative/high/low usually means. |
| `comparison_context` | What the user should compare it against: prior period, benchmark, threshold, or peer metric. |
| `current_context_note` | Short sentence generated from current payload state when possible. |
| `caveats` | Data limitations, omission conditions, or non-comparable cases. |

### Analyst-authored terminology hardening

The current chart tooltip demonstrates why this contract is needed:

- `PnL` is too terse for a primary interpretation surface.
- `Trendline` is mathematical shorthand without analytical framing.
- `S&P 500 Proxy` and `NASDAQ-100 Proxy` need explicit normalization context.
- tooltip action labels such as `Analyze Risk` and `Export CSV` create false affordances when not wired.

Approved replacement guidance:

| Current label | Preferred label | Reason |
|---|---|---|
| `PnL` | `Unrealized P&L vs cost basis` | Makes basis and scope explicit. |
| `Trendline` | `Trend estimate` | Clarifies that this is a derived guide, not observed truth. |
| `S&P 500 Proxy` | `S&P 500 benchmark (normalized)` | States comparison role and normalization behavior. |
| `NASDAQ-100 Proxy` | `NASDAQ-100 benchmark (normalized)` | States comparison role and normalization behavior. |

### Current-context note examples

- `Unrealized P&L vs cost basis`: "Current market value is above total open cost basis by `$X`; this is not the same as selected-period return."
- `Portfolio total return`: "Selected period ended `Y%` below the first observed value in this window."
- `Benchmark spread`: "Portfolio outperformed the best available benchmark by `Z` percentage points in the selected window."
- `Max drawdown`: "Worst observed drop from prior peak within current scope was `N%`."

## Action Placement and False-Affordance Contract (Task 1.9)

Interactive controls inside transient hover tooltips are prohibited for primary workflow actions unless they are fully functional, keyboard-accessible, and stable on touch devices.

### Rules

- Hover tooltip content is informational first; it should not be the only place where an action exists.
- Route-changing actions belong in persistent chart headers, section actions, or stable context panels.
- Export actions belong in persistent action groups with explicit file scope and format labels.
- Placeholder or decorative buttons that do nothing are forbidden on promoted analytical surfaces.
- If an action is not implemented yet, the UI must omit it instead of implying availability.

### Phase F application to current trend tooltip

- Remove or relocate `Analyze Risk` from the tooltip into a stable surface that deep-links to `/portfolio/risk` with preserved `period`.
- Remove or relocate `Export CSV` into a stable section action only when one deterministic export contract exists.
- Keep the tooltip focused on date-scoped values, spread context, and explainability entry points.

## Goals / Non-Goals

**Goals:**
- Deliver an analyst-owned KPI placement model that fixes route intent boundaries (`Home`, `Analytics`, `Risk`, `Quant/Reports`).
- Eliminate chart duplication and spacing drift by standardizing reusable chart composition primitives.
- Promote Quant report workflows to a dedicated workspace surface with explicit lifecycle state handling.
- Keep backend report APIs route-agnostic so UX relocation does not require Home-coupled contracts.
- Extend release-readiness gates to verify chart-consistency and promoted Quant/Reports interaction behavior.

**Non-Goals:**
- Redesigning or replacing backend quant computation methodology.
- Replacing the chart library (`Recharts`) or initiating framework migration work.
- Broad visual-brand redesign outside workspace IA and chart consistency scope.
- Adding cross-user report persistence or long-lived report artifact storage beyond existing bounded lifecycle.

## Decisions

### Decision 1: Introduce a dedicated `Quant/Reports` route surface in workspace IA
- Decision: Treat report generation/retrieval as a first-class workspace surface (or explicitly promoted equivalent), not as an embedded Home-owned workflow.
- Rationale: report tasks are analytical workflows with distinct state transitions and should not compete with Home snapshot comprehension.
- Alternatives considered:
  - Keep report actions on Home and improve copy only: rejected due continued route-purpose ambiguity.
  - Move report actions to Risk: rejected because reports span broader analytical usage than risk-only interpretation.

### Decision 2: Enforce a route-scoped KPI governance catalog before UI reshaping
- Decision: Require a documented KPI matrix with analyst ownership, formula narrative, and route placement prior to implementation finalization.
- Rationale: visual cleanup without KPI ownership often reintroduces duplication and semantic drift in later slices.
- Alternatives considered:
  - Allow implementation-first KPI decisions: rejected due high rework risk.
  - Keep KPI ownership implicit in component names: rejected because it is not auditable or testable.

### Decision 3: Standardize chart composition via shared primitives and tokenized layout contracts
- Decision: Define one chart composition contract for container sizing, spacing, and module headers shared across Home/Analytics/Risk.
- Rationale: deterministic UI contracts reduce duplication and make regression tests reliable.
- Alternatives considered:
  - Route-local chart wrappers per page: rejected because it preserves inconsistency and duplicated logic.
  - One large monolithic chart shell for all routes: rejected due low flexibility for route-specific narratives.

### Decision 4: Keep report API contracts route-agnostic and explicitly stateful
- Decision: backend report endpoints remain independent of Home-specific context and provide explicit scope/lifecycle metadata for dedicated Quant/Reports rendering.
- Rationale: frontend IA changes should not require endpoint redefinition or hidden route assumptions.
- Alternatives considered:
  - Introduce Home-origin flags in API requests: rejected due unnecessary coupling.
  - Infer report lifecycle from missing fields client-side: rejected by explicit-state/fail-fast rules.

### Decision 5: Add release-readiness gates specific to Phase F risks
- Decision: release validation must include chart-consistency checks and dedicated Quant/Reports state + accessibility coverage.
- Rationale: baseline lint/build/test passing is insufficient for this slice’s UX contract risks.
- Alternatives considered:
  - Rely on manual QA only: rejected due low repeatability and weak change evidence.

## Risks / Trade-offs

- [Risk] KPI governance review can slow implementation throughput.
  Mitigation: lock a minimum viable KPI catalog first, then iterate with explicit follow-up tasks.

- [Risk] Promoting a new workspace surface may increase navigation complexity.
  Mitigation: keep deterministic route labels and preserve existing deep-link behavior.

- [Risk] Chart standardization can cause layout regressions in edge viewport sizes.
  Mitigation: add targeted responsive tests and include route-level visual evidence capture in validation.

- [Risk] Existing report interactions may rely on Home-local assumptions hidden in frontend state hooks.
  Mitigation: add fail-first tests that reproduce current coupling before refactoring hooks and API clients.

## Migration Plan

1. Lock spec and KPI governance artifacts for Phase F before implementation starts.
2. Add fail-first frontend/backend tests that capture current chart duplication, spacing inconsistency, and Home-coupled report flow behavior.
3. Refactor workspace routing and composition primitives to introduce dedicated Quant/Reports context and shared chart layout contracts.
4. Update API client/hook layers to consume report contracts from route-agnostic flows.
5. Run frontend/backend/OpenSpec validation gates and capture evidence artifacts.
6. Rollback strategy: disable new route exposure and restore prior workspace composition while retaining backward-compatible report endpoints.

## Open Questions

None.
