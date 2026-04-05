# portfolio-timeseries-signals Specification

## Purpose
TBD - created by archiving change phase-i-ml-timeseries-signal-and-forecasting. Update Purpose after archive.
## Requirements
### Requirement: Portfolio time-series signals SHALL be deterministic for a fixed snapshot
The system SHALL compute time-series signals from approved read-only ledger and market snapshots, and equivalent snapshot inputs SHALL produce equivalent signal outputs.

#### Scenario: Equivalent inputs produce identical signal payloads
- **WHEN** two requests use the same scope, snapshot identifiers, and window parameters
- **THEN** the system returns identical signal identifiers and values
- **THEN** no randomized model state changes the output

#### Scenario: Insufficient history returns explicit unavailable state
- **WHEN** the requested scope does not have minimum history for one or more required signal windows
- **THEN** the system returns state `unavailable` with factual missing-history reasons
- **THEN** no synthetic or imputed signal values are fabricated silently

### Requirement: Portfolio time-series signals SHALL include freshness and provenance metadata
The system SHALL attach snapshot provenance and freshness metadata to every signal response so downstream consumers can determine whether outputs are current and auditable.

#### Scenario: Response carries snapshot references and timestamps
- **WHEN** signals are returned for any scope
- **THEN** the payload includes `as_of_ledger_at`, `as_of_market_at`, and source snapshot identifiers
- **THEN** the payload includes evaluation timestamp and configured freshness policy metadata

#### Scenario: Stale source data is surfaced explicitly
- **WHEN** market or ledger source timestamps exceed configured freshness bounds
- **THEN** the response state is `stale` with stale-source details
- **THEN** the client does not need to infer staleness from missing fields

### Requirement: Portfolio time-series signals SHALL support portfolio and instrument scopes
The system SHALL provide a unified signal contract for both aggregate portfolio scope and single instrument scope with explicit scope metadata.

#### Scenario: Portfolio scope request
- **WHEN** a client requests scope `portfolio`
- **THEN** the system returns aggregate portfolio signal values and scope metadata `portfolio`
- **THEN** symbol-specific fields are omitted or null by schema contract

#### Scenario: Instrument scope request
- **WHEN** a client requests scope `instrument_symbol` with a valid symbol
- **THEN** the system returns signal values computed for that instrument only
- **THEN** the response includes the validated instrument symbol and scope metadata

### Requirement: Time-series signal API SHALL expose one frozen lifecycle contract
The system SHALL expose `GET /api/portfolio/ml/signals` with a shared lifecycle envelope so clients can process readiness uniformly.

#### Scenario: Ready signal contract uses frozen envelope fields
- **WHEN** required signal inputs and CAPM inputs are present and within freshness policy
- **THEN** response includes `state=ready` plus `state_reason_code`, `state_reason_detail`, `evaluated_at`, `as_of_ledger_at`, `as_of_market_at`, and `freshness_policy`
- **THEN** response includes signal rows with stable `signal_id` values and CAPM metrics with provenance

#### Scenario: Unavailable, stale, and error states are explicit and non-null
- **WHEN** required inputs are insufficient, stale, or service execution fails
- **THEN** response state is one of `unavailable`, `stale`, or `error`
- **THEN** `state_reason_code` and `state_reason_detail` are populated with factual cause metadata

### Requirement: Portfolio time-series signals SHALL expose stable signal identifiers
The system SHALL publish stable signal identifiers and units so consumers can render and compare values across releases.

#### Scenario: Stable IDs are returned for known signals
- **WHEN** signal payload is produced
- **THEN** each signal row includes a stable `signal_id`, unit metadata, and interpretation band metadata
- **THEN** signal labels can evolve without changing identifier semantics

### Requirement: Portfolio time-series signals SHALL include CAPM portfolio-management metrics
The system SHALL compute CAPM metrics for supported scopes using explicit benchmark and risk-free inputs, and SHALL expose metric provenance in the response contract.

#### Scenario: CAPM metrics are returned with provenance
- **WHEN** required benchmark history and risk-free inputs are available for the requested scope
- **THEN** the response includes CAPM metrics `beta`, `alpha`, `expected_return`, and `market_premium`
- **THEN** the response includes benchmark identifier, risk-free source, and annualization metadata

#### Scenario: Missing CAPM inputs produce explicit unavailable state
- **WHEN** benchmark history or risk-free inputs are missing, stale, or below minimum window requirements
- **THEN** CAPM response state is `unavailable` with specific missing-input reasons
- **THEN** no inferred benchmark or synthetic risk-free fallback is applied silently
