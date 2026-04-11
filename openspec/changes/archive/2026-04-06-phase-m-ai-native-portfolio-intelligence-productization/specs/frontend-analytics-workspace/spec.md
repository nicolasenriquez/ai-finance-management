## ADDED Requirements

### Requirement: Frontend workspace SHALL expose decision-lens navigation for AI-native portfolio workflows
The frontend SHALL provide explicit decision-lens navigation that includes `Dashboard`, `Holdings`, `Performance`, `Risk`, `Rebalancing`, `Copilot`, and `Transactions` surfaces without breaking existing deep links.

#### Scenario: Decision-lens navigation is available
- **WHEN** a user opens portfolio workspace navigation
- **THEN** the decision-lens route set is visible with stable route identifiers
- **THEN** existing compatible links resolve through migration-safe redirects or alias routing

### Requirement: Dashboard lens SHALL prioritize command-center first-viewport decisions
The Dashboard lens SHALL render command-center metrics and insight cards in the first viewport and SHALL avoid advanced-module overload before users make first-pass decisions.

#### Scenario: Dashboard first viewport is decision-first
- **WHEN** dashboard data loads successfully
- **THEN** first viewport contains net worth posture, return context, drawdown/concentration highlights, and top insights
- **THEN** advanced diagnostics are moved to secondary sections or dedicated lenses

### Requirement: Risk and rebalancing lenses SHALL surface chart modules for explainable decision support
The workspace SHALL render bounded chart modules for correlation, contribution-to-risk, frontier comparison, and scenario deltas with explicit unavailable states.

#### Scenario: Risk and rebalancing modules show explicit lifecycle states
- **WHEN** required backend datasets are ready, stale, unavailable, or errored
- **THEN** each module displays one explicit trust state with actionable context
- **THEN** modules do not present placeholder values as valid analysis

### Requirement: Dashboard lens SHALL include what-changed insight panel
The Dashboard lens SHALL include a deterministic "what changed" panel summarizing material shifts in exposures, risk posture, or contribution drivers across the selected period.

#### Scenario: What-changed panel links to underlying lenses
- **WHEN** material changes are detected for selected period/scope
- **THEN** panel entries include concise summary text and links to relevant risk/performance/rebalancing details
- **THEN** each entry references as-of metadata so users can validate recency
