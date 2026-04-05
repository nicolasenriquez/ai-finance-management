# frontend-analytics-workspace Specification

## Purpose
TBD - created by archiving change expand-frontend-ux-and-analytics-workspace. Update Purpose after archive.
## Requirements
### Requirement: Frontend analytics workspace SHALL expose deterministic multi-route navigation
The frontend SHALL provide a portfolio analytics workspace with route-level navigation for `Home`, `Analytics`, `Risk`, and `Transactions`, while preserving deterministic access to existing summary and lot-detail flows.

#### Scenario: Workspace navigation renders canonical routes
- **WHEN** a user opens the portfolio workspace
- **THEN** the UI exposes navigable sections for `Home`, `Analytics`, `Risk`, and `Transactions`
- **THEN** each section resolves to a stable route and does not break existing lot-detail deep links

### Requirement: Home route SHALL foreground first-viewport portfolio context
The Home route SHALL render first-viewport trust context with executive KPI summary cards and at least one trend visualization backed by typed analytics responses, while limiting the route to preview-oriented analytics rather than full report workflow ownership.

#### Scenario: Home route shows executive snapshot without owning full report workflow
- **WHEN** Home data loads successfully
- **THEN** the first viewport includes portfolio-level KPI cards and one trend chart
- **THEN** the screen displays data freshness/provenance context and does not rely on implied values
- **THEN** report-generation actions are presented as navigation into dedicated analytical context instead of full workflow execution on Home

### Requirement: Analytics route SHALL provide chart-driven performance and attribution views
The Analytics route SHALL provide chart modules for performance and contribution breakdown using server-provided analytics payloads, including explicit empty/error behavior when inputs are unavailable.

#### Scenario: Analytics route handles ready and unavailable states explicitly
- **WHEN** analytics endpoints return data or return an explicit failure
- **THEN** the route renders chart modules for successful responses
- **THEN** unavailable or failed responses render explicit fallback states with retry or scope messaging

### Requirement: Workspace chart foundation SHALL remain `Recharts` for v1 unless evidence-gated review approves a change
The analytics workspace SHALL use `Recharts` as the v1 chart foundation. A chart-library switch SHALL require an explicit decision artifact grounded in route-level evidence.

#### Scenario: Chart-library switch is blocked without route-level evidence
- **WHEN** chart-library replacement is proposed during v1 delivery
- **THEN** the proposal includes route-level evidence from `/portfolio/home`, `/portfolio/analytics`, and `/portfolio/risk` covering CWV/accessibility blockers and maintainability impact
- **THEN** without that evidence and explicit approval, `Recharts` remains the required chart foundation

### Requirement: Analytics controls SHALL constrain chart-period inputs to approved backend enum values
The Analytics route SHALL expose chart-period controls aligned with approved backend period values (`30D`, `90D`, `252D`, `MAX`) and SHALL prevent unsupported period submissions.

#### Scenario: Unsupported period selection is not submitted
- **WHEN** a user interacts with chart-period controls on analytics views
- **THEN** selectable values are limited to approved backend-supported enum values
- **THEN** the route does not submit unsupported period values to analytics endpoints

### Requirement: Risk route SHALL present bounded risk insight with explicit scope labels
The Risk route SHALL render risk estimators and related visualizations only from approved backend estimator contracts and SHALL display scope limitations when estimator inputs are insufficient.

#### Scenario: Risk route fails explicitly on insufficient estimator input
- **WHEN** estimator endpoints report insufficient historical coverage or unsupported scope
- **THEN** the route shows an explicit risk-unavailable state with factual reason
- **THEN** the UI does not display placeholder risk percentages as if they were valid

### Requirement: Risk route SHALL surface estimator methodology metadata without hidden defaults
The Risk route SHALL display estimator methodology metadata provided by backend contracts (for example return basis, window, annualization basis, and as-of context) so users can interpret risk values without implied assumptions.

#### Scenario: Risk cards include methodology context from API metadata
- **WHEN** risk estimator data loads successfully
- **THEN** the route renders methodology context adjacent to risk values/charts
- **THEN** users can determine how displayed metrics were computed without reading external documentation

### Requirement: Transactions route SHALL be ledger-history scoped in v1
The Transactions route SHALL present persisted ledger-event history as its v1 scope and SHALL not co-mingle market-refresh operation diagnostics in this slice.

#### Scenario: Transactions route renders ledger events only
- **WHEN** the user opens the Transactions route
- **THEN** the displayed list/table reflects persisted ledger events with deterministic ordering/filter behavior
- **THEN** market-refresh operation diagnostics are not rendered in this v1 route contract

#### Scenario: Diagnostics follow-up scope remains explicit and deferred
- **WHEN** users need market-refresh diagnostics visibility
- **THEN** the requirement is handled by a dedicated follow-up operator-facing capability
- **THEN** the v1 `Transactions` route contract remains ledger-history-only

### Requirement: Frontend analytics workspace SHALL expose a dedicated Quant/Reports surface
The frontend SHALL provide a dedicated `Quant/Reports` workspace surface for report generation and advanced quant diagnostics so HTML report workflows are not buried in the Home route.

#### Scenario: Quant report workflow starts from dedicated surface
- **WHEN** a user needs to generate or retrieve a Quant report
- **THEN** the workflow entry is available from a dedicated `Quant/Reports` workspace surface
- **THEN** Home remains focused on executive snapshot context and does not serve as the primary report-generation surface

### Requirement: Workspace chart modules SHALL follow one shared composition contract
The frontend SHALL enforce one chart composition contract across Home, Analytics, and Risk routes, including responsive container sizing, consistent panel spacing, and shared chart header semantics.

#### Scenario: Chart layout tokens are consistent across routes
- **WHEN** chart modules render in Home, Analytics, and Risk
- **THEN** they use the same spacing and container sizing tokens defined by shared workspace primitives
- **THEN** route-specific chart modules do not introduce unreviewed one-off sizing or spacing behavior

#### Scenario: Mixed-unit risk payloads avoid misleading single-axis charting
- **WHEN** the Risk route receives estimator metrics that are not unit-compatible on one axis
- **THEN** the UI applies a guardrail state instead of rendering a misleading mixed-unit single-axis bar chart
- **THEN** users still receive deterministic metric-card interpretation context and methodology metadata

### Requirement: Promoted metrics SHALL provide accessible explainability affordances
The frontend SHALL expose accessible explainability affordances for promoted KPIs and important chart metrics so users can inspect what the metric means, why it matters, and how to interpret the current reading.

#### Scenario: User inspects KPI explanation from one stable affordance
- **WHEN** a user focuses, hovers, or activates an info affordance for a promoted KPI or chart metric
- **THEN** the UI renders definition, relevance, interpretation, and caveat content without requiring hidden hover-only access
- **THEN** the content remains keyboard-accessible and readable on touch devices

### Requirement: Analytical actions SHALL not rely on false affordances
The frontend SHALL not render non-functional analytical actions, and primary actions SHALL not live only inside transient hover tooltips.

#### Scenario: Chart tooltip avoids dead controls
- **WHEN** chart tooltip content is shown for one analytical data point
- **THEN** any action displayed there is fully functional, accessible, and duplicated in one stable surface if it drives workflow navigation or export
- **THEN** placeholder controls that do nothing are not rendered

### Requirement: Risk route SHALL provide timeline and distribution modules for interpretation depth
The Risk route SHALL render timeline and distribution modules (drawdown path, rolling estimators, return distribution) using typed backend datasets and explicit scope/period controls.

#### Scenario: Risk route renders timeline and distribution modules for selected scope
- **WHEN** risk-evolution datasets load successfully
- **THEN** the route renders timeline and distribution modules with explicit as-of and methodology context
- **THEN** module data aligns to the selected period and scope controls

### Requirement: Risk route timeline interactions SHALL be user-controllable and accessible
Risk timeline modules SHALL support deterministic series visibility controls and keyboard-reachable interactions.

#### Scenario: Users can toggle timeline series visibility deterministically
- **WHEN** a user toggles one or more timeline series controls
- **THEN** the chart updates to hide/show only selected series deterministically
- **THEN** controls are keyboard reachable and expose accessible labels/state

### Requirement: Quant/Reports route SHALL expose Monte Carlo diagnostics workflow states
The Quant/Reports route SHALL provide simulation controls and explicit lifecycle rendering for Monte Carlo diagnostics (`loading`, `error`, `unavailable`, `ready`).

#### Scenario: Monte Carlo module renders explicit workflow states
- **WHEN** a user triggers or revisits Monte Carlo diagnostics
- **THEN** the route renders one explicit lifecycle state for the current simulation request
- **THEN** UI copy communicates assumptions, caveats, and current context without hidden defaults

### Requirement: Explainability affordances SHALL include threshold-context interpretation for promoted risk and quant KPIs
Promoted KPI explainability affordances SHALL include concise threshold-context guidance (for example low/moderate/high-risk interpretation).

#### Scenario: Metric explainability includes threshold-context interpretation copy
- **WHEN** a user opens explainability for a promoted risk or simulation metric
- **THEN** the popover includes definition, why-it-matters, and threshold-context interpretation guidance
- **THEN** the copy reflects current metric values when deterministic context is available

### Requirement: Quant/Reports Monte Carlo module SHALL render three profile scenarios in one panoramic comparison view
The Monte Carlo module SHALL provide a side-by-side readable comparison for `Conservative`, `Balanced`, and `Growth` profile outcomes without requiring tooltip-only inspection.

#### Scenario: Three profile outcomes are visible and comparable at once
- **WHEN** profile comparison mode is enabled
- **THEN** the UI renders exactly three stable profile rows/cards in fixed order (`Conservative`, `Balanced`, `Growth`)
- **THEN** each profile shows thresholds and probability outcomes in one glance-friendly layout

### Requirement: Monte Carlo profile comparison controls SHALL coexist with manual parameter controls
The Monte Carlo module SHALL preserve manual parameter editing while adding profile-comparison controls for fast scenario switching.

#### Scenario: Users can toggle comparison and apply profile presets without losing manual workflow
- **WHEN** a user interacts with comparison controls (`Enable profile compare`, `Calibration basis`, `Apply profile`)
- **THEN** manual controls (`sims`, horizon, `bust`, `goal`, `seed`) remain editable and deterministic
- **THEN** users can run one simulation and inspect both manual and profile-based contexts

### Requirement: Workspace KPI copy SHALL use portfolio P&L semantics explicitly
Frontend KPI copy SHALL distinguish portfolio P&L concepts (realized, unrealized, period change, total return) and SHALL avoid business income-statement terminology that is out of scope for portfolio diagnostics.

#### Scenario: Portfolio P&L terminology remains route-consistent
- **WHEN** P&L-related KPI labels and explanations are rendered in Home, Analytics, and Quant/Reports surfaces
- **THEN** labels align with investment portfolio semantics and include concise interpretation context
- **THEN** business statement terms (for example `COGS`, `OPEX`, `EBITDA`) are not presented as portfolio KPI fields in this workspace

### Requirement: Home route SHALL provide a portfolio-health synthesis panel
The Home route SHALL present a compact portfolio-health synthesis module with explicit status, score, profile posture, and key drivers so users can interpret portfolio condition without scanning all advanced KPIs first.

#### Scenario: Health panel renders deterministic summary and drivers
- **WHEN** summary and health synthesis data are available
- **THEN** Home renders one health summary panel with `health_label`, score, selected profile posture, and top supporting/risk drivers
- **THEN** the panel includes a clear caveat that health synthesis is interpretation support and not financial advice

### Requirement: Health interpretation SHALL remain route-consistent and drill-down friendly
Workspace routes SHALL preserve a consistent health narrative by linking aggregate health interpretation to Risk and Quant/Reports modules.

#### Scenario: Health panel drill-down exposes consistent context in Risk and Quant modules
- **WHEN** a user opens health details from Home
- **THEN** Risk route reflects risk-pillar context for the same period/scope/profile
- **THEN** Quant/Reports route reflects scenario sensitivity context aligned with the same health profile posture

### Requirement: Workspace SHALL prioritize core KPIs before advanced diagnostics
The workspace SHALL present a deterministic KPI-priority structure that promotes a `Core 10` interpretation set while keeping advanced diagnostics accessible as secondary detail.

#### Scenario: Core and advanced KPI layers are visually and semantically separated
- **WHEN** KPI sections are rendered in Home, Risk, and Quant/Reports
- **THEN** users can identify the core interpretation layer without scanning advanced metrics first
- **THEN** advanced metrics remain available without being required for first-pass health interpretation

### Requirement: Quant lens table SHALL preserve professional dense-table readability
The Quant/Reports period lens SHALL use deterministic table semantics with aligned period columns and tabular numeric rhythm for quick cross-period interpretation.

#### Scenario: Quant lens rows remain aligned and scannable
- **WHEN** quant lens rows are rendered for `30D`, `90D`, and `252D`
- **THEN** each metric row aligns values to fixed period columns without visual drift
- **THEN** numeric cells render with consistent alignment/typography suitable for dense analytical comparison

### Requirement: Quant report lifecycle controls SHALL be compact and action-prioritized
The Quant/Reports lifecycle module SHALL render scope controls, primary generate action, and lifecycle status in one compact action surface.

#### Scenario: Lifecycle action hierarchy is explicit and compact
- **WHEN** the lifecycle module is rendered in `unavailable`, `loading`, `error`, or `ready`
- **THEN** the primary generate action remains visually dominant and adjacent to scope controls
- **THEN** lifecycle detail states remain accessible without oversized vertical blank space

### Requirement: Contribution leaders tables SHALL expose directional semantics explicitly
Contribution leaders surfaces SHALL present signed contribution, net share, and absolute share with explicit labels and deterministic default ordering.

#### Scenario: Users can interpret contribution direction and concentration in one scan
- **WHEN** contribution leaders rows are rendered
- **THEN** labels distinguish directional (`net share`) versus concentration (`abs share`) context explicitly
- **THEN** rows are ordered deterministically by absolute contribution concentration

### Requirement: Portfolio hierarchy SHALL default to sector-collapsed view and support sortable headers
The hierarchy table SHALL reduce first-load noise by defaulting sector groups to collapsed, and SHALL provide explicit sortable-header affordances.

#### Scenario: Hierarchy opens collapsed and supports explicit sorting
- **WHEN** the hierarchy module first loads in sector grouping
- **THEN** sector groups are collapsed by default until expanded by the user
- **THEN** sortable columns expose visible arrow-state affordances and deterministic ordering behavior
