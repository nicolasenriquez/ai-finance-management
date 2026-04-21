## ADDED Requirements

### Requirement: Home route SHALL render a contract-backed portfolio-versus-benchmark hero chart
The `/portfolio/home` route SHALL render one primary portfolio-versus-benchmark chart module backed by typed API contracts, replacing pseudo-chart placeholders for first-viewport interpretation.

#### Scenario: Home hero chart renders with real contract-backed values
- **WHEN** home summary and trend datasets load successfully
- **THEN** the first viewport shows one contract-backed portfolio-versus-benchmark hero chart
- **THEN** the route does not substitute static placeholder rows as if they were charted evidence

### Requirement: Analytics route SHALL render contract-backed explainability charts
The `/portfolio/analytics` route SHALL render relative-performance, contribution-ranking, and attribution-waterfall chart modules backed by typed contribution and summary contracts.

#### Scenario: Analytics explainability charts are rendered from real payloads
- **WHEN** analytics datasets resolve successfully
- **THEN** the route renders contract-backed performance, ranking, and waterfall chart modules
- **THEN** fallback states are explicit for loading, empty, unavailable, and error outcomes

### Requirement: Risk route SHALL render contract-backed fragility charts
The `/portfolio/risk` route SHALL render drawdown, rolling-risk, and return-distribution chart modules from approved risk and portfolio contracts.

#### Scenario: Risk fragility modules expose downside context with real data
- **WHEN** risk datasets resolve for the selected route context
- **THEN** the route renders drawdown, rolling-risk, and distribution charts with explicit scope context
- **THEN** the route avoids static pseudo-series for primary fragility interpretation

### Requirement: Primary chart containers SHALL maintain stable responsive geometry
Primary chart modules SHALL use stable parent dimensions and responsive chart containers so loading-to-ready transitions avoid layout shift and chart clipping.

#### Scenario: Chart geometry remains stable across route state transitions
- **WHEN** one primary chart module transitions from loading to ready
- **THEN** container geometry remains stable across the transition
- **THEN** chart axes and tooltips remain readable without overflow-induced clipping

### Requirement: Chart modules SHALL preserve explicit unit semantics
Chart modules SHALL preserve unit-safe axes and tooltip semantics, and SHALL avoid mixed-unit overlays that imply comparability when units differ.

#### Scenario: Mixed-unit payloads trigger guardrails instead of misleading plots
- **WHEN** chart input metrics are not unit-compatible in one axis space
- **THEN** the module renders an explicit guardrail state or split presentation
- **THEN** the UI does not present misleading shared-axis charts for incompatible units
