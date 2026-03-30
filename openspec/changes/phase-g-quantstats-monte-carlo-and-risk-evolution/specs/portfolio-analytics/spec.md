## ADDED Requirements

### Requirement: Portfolio analytics API SHALL expose risk-evolution chart datasets
The portfolio analytics API SHALL provide chart-ready risk-evolution datasets for approved scopes and periods, including drawdown path and rolling estimator series.

#### Scenario: Risk-evolution datasets return drawdown and rolling series
- **WHEN** a client requests risk-evolution analytics for a supported scope and period
- **THEN** the API returns ordered drawdown-path points and rolling-series points with explicit timestamps
- **THEN** the payload includes methodology metadata required for frontend interpretation

### Requirement: Portfolio analytics API SHALL expose deterministic return-distribution datasets
The portfolio analytics API SHALL provide deterministic return-distribution bucket outputs from persisted return history for approved scope and period inputs.

#### Scenario: Return-distribution buckets are deterministic for equivalent input state
- **WHEN** the same persisted state, scope, period, and bucket policy are requested repeatedly
- **THEN** the API returns the same bucket boundaries and counts
- **THEN** the response includes bucket-policy metadata used for chart rendering

### Requirement: Scope semantics SHALL remain explicit and consistent across chart analytics contracts
The API SHALL enforce explicit scope semantics for risk-evolution and return-distribution datasets using the existing `scope` and `instrument_symbol` contract posture.

#### Scenario: Missing symbol for instrument scope is rejected explicitly
- **WHEN** a client requests scope `instrument_symbol` without a valid `instrument_symbol` parameter
- **THEN** the API returns explicit client-facing validation failure
- **THEN** the service does not infer or default symbol scope implicitly

### Requirement: Portfolio analytics contracts SHALL provide investment P&L decomposition semantics
Portfolio analytics contracts SHALL support investment P&L decomposition context (realized, unrealized, period change, total return context) for dashboard storytelling without mixing business-income-statement semantics.

#### Scenario: P&L decomposition fields are explicit and portfolio-scoped
- **WHEN** a client requests portfolio analytics summary/decomposition data
- **THEN** response fields and metadata distinguish realized and unrealized components plus period-level movement context
- **THEN** contracts remain aligned to portfolio investment semantics and do not introduce company-income-statement line items

### Requirement: Portfolio analytics API SHALL expose deterministic health-synthesis outputs
The API SHALL expose a deterministic portfolio-health synthesis payload that aggregates approved KPI groups into explicit pillar scores and a bounded aggregate health label.

#### Scenario: Health synthesis payload includes score, label, pillars, and drivers
- **WHEN** a client requests portfolio health interpretation for a supported scope/period
- **THEN** the response includes `health_score`, `health_label`, `profile_posture`, and fixed-order pillar outputs
- **THEN** the response includes deterministic key drivers and caveat metadata describing any missing/omitted context

### Requirement: Health synthesis SHALL support profile posture weighting explicitly
The API SHALL support posture-specific weighting (`conservative`, `balanced`, `aggressive`) and SHALL expose effective weights used for score construction.

#### Scenario: Profile posture selection changes score deterministically
- **WHEN** equivalent data is requested with different profile posture values
- **THEN** score and label outputs follow the configured posture weighting deterministically
- **THEN** response metadata exposes effective weights and applied threshold policy version
