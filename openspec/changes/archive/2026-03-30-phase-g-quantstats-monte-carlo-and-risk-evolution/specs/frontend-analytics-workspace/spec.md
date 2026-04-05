## ADDED Requirements

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
