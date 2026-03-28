## ADDED Requirements

### Requirement: Frontend analytics workspace SHALL expose deterministic multi-route navigation
The frontend SHALL provide a portfolio analytics workspace with route-level navigation for `Home`, `Analytics`, `Risk`, and `Transactions`, while preserving deterministic access to existing summary and lot-detail flows.

#### Scenario: Workspace navigation renders canonical routes
- **WHEN** a user opens the portfolio workspace
- **THEN** the UI exposes navigable sections for `Home`, `Analytics`, `Risk`, and `Transactions`
- **THEN** each section resolves to a stable route and does not break existing lot-detail deep links

### Requirement: Home route SHALL foreground first-viewport portfolio context
The Home route SHALL render first-viewport trust context with KPI summary cards, freshness/provenance labels, and at least one trend visualization that is backed by typed analytics responses.

#### Scenario: Home route shows KPI cards and trend context
- **WHEN** Home data loads successfully
- **THEN** the first viewport includes portfolio-level KPI cards and one trend chart
- **THEN** the screen displays data freshness/provenance context and does not rely on implied values

### Requirement: Analytics route SHALL provide chart-driven performance and attribution views
The Analytics route SHALL provide chart modules for performance and contribution breakdown using server-provided analytics payloads, including explicit empty/error behavior when inputs are unavailable.

#### Scenario: Analytics route handles ready and unavailable states explicitly
- **WHEN** analytics endpoints return data or return an explicit failure
- **THEN** the route renders chart modules for successful responses
- **THEN** unavailable or failed responses render explicit fallback states with retry or scope messaging

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
