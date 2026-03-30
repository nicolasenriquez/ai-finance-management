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
