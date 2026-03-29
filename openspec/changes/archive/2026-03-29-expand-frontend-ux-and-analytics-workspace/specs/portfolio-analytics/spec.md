## ADDED Requirements

### Requirement: Portfolio analytics API SHALL provide chart-ready portfolio time-series
The system SHALL provide a read-only portfolio time-series endpoint that returns ordered portfolio value and PnL points for approved periods so frontend chart modules can render trend analytics without client-side inference.

#### Scenario: Time-series endpoint returns ordered points for selected period
- **WHEN** a client requests portfolio time-series for a supported window
- **THEN** the API returns chronologically ordered points with explicit timestamps and value fields
- **THEN** the payload is deterministic for the same persisted input state and period parameters

### Requirement: Portfolio analytics time-series responses SHALL expose explicit temporal interpretation metadata
The system SHALL include explicit temporal interpretation metadata for chart-oriented time-series responses, including at minimum frequency context, timezone basis, and selected period/window parameters.

#### Scenario: Time-series payload includes temporal context metadata
- **WHEN** the API returns chart-oriented time-series data
- **THEN** the response includes explicit temporal interpretation metadata required to render and compare points correctly
- **THEN** frontend consumers do not infer hidden frequency or timezone defaults

### Requirement: Portfolio analytics API SHALL provide contribution breakdown by instrument for selected periods
The system SHALL provide a contribution breakdown endpoint that returns per-symbol aggregates for the selected period to support attribution visualizations.

#### Scenario: Contribution endpoint returns per-symbol aggregates
- **WHEN** a client requests contribution analytics for a supported period
- **THEN** the API returns one row per instrument symbol with contribution-related aggregates
- **THEN** totals are derived from persisted ledger and approved market-data inputs only

### Requirement: Portfolio chart analytics endpoints SHALL enforce a bounded v1 period enum
The system SHALL support only the approved v1 chart period enum (`30D`, `90D`, `252D`, `MAX`) for time-series and contribution analytics requests and SHALL reject unsupported period values explicitly.

#### Scenario: Unsupported chart period is rejected explicitly
- **WHEN** a client requests chart analytics with a period outside the approved v1 enum
- **THEN** the API returns an explicit client-facing validation failure
- **THEN** the service does not coerce unsupported periods into implicit defaults

## MODIFIED Requirements

### Requirement: Portfolio analytics responses expose explicit ledger-state consistency metadata
The system SHALL include explicit ledger consistency metadata in grouped summary, lot-detail, and newly added chart-oriented analytics responses so clients can determine the persisted ledger state used for computation.

#### Scenario: Summary, lot detail, and chart responses include ledger as-of metadata
- **WHEN** the system returns grouped summary, lot detail, or chart-oriented portfolio analytics responses
- **THEN** the payload includes explicit ledger-state consistency metadata
- **THEN** clients can determine the persisted ledger state time used for computation

### Requirement: Portfolio summary API exposes only ledger-supported KPI fields in v1
The system SHALL expose only analytics fields that are fully supported by current ledger truth, persisted market-data boundaries, and frozen accounting policy, without silently inventing unsupported price-dependent or FX-dependent values.

#### Scenario: Summary row includes only approved KPI and market-enriched fields
- **WHEN** a grouped portfolio summary row is returned
- **THEN** it includes approved ledger and bounded market-enriched fields defined by the active portfolio analytics contract
- **THEN** unsupported FX-sensitive or inferred valuation fields are excluded and represented through explicit failure or nullability semantics
