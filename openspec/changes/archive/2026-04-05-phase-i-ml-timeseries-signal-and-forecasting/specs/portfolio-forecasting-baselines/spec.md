## ADDED Requirements

### Requirement: Forecast training SHALL use walk-forward evaluation over approved baseline model family
The system SHALL train and evaluate forecasting candidates using walk-forward time splits and SHALL limit v1 candidates to approved baseline models.

#### Scenario: Approved baseline candidates are evaluated
- **WHEN** a training/evaluation run is executed
- **THEN** candidates include naive, seasonal-naive, EWMA or Holt-family baseline, ARIMA-family baseline, and ridge lag-regression baseline
- **THEN** temporal splits preserve chronological ordering with no future leakage into training windows

#### Scenario: Leakage checks fail explicitly
- **WHEN** feature generation or split construction violates temporal boundaries
- **THEN** the run is marked failed with explicit leakage reason metadata
- **THEN** no candidate is promoted from that run

### Requirement: Forecast publication SHALL require baseline improvement and calibration gates
The system SHALL publish a champion forecast snapshot only when policy gates are satisfied against naive baseline metrics and interval calibration constraints.

#### Scenario: Candidate passes quality gates and is promoted
- **WHEN** a candidate improves walk-forward `wMAPE` by at least `5.0%` versus naive baseline
- **AND** no horizon regresses by more than `2.0%` `wMAPE` versus naive baseline
- **AND** 80% interval empirical coverage stays within `[0.72, 0.88]`
- **THEN** the system records that candidate as the new champion snapshot
- **THEN** forecast endpoint state is `ready` for horizons covered by champion metadata

#### Scenario: Candidate fails quality gates
- **WHEN** all candidates fail one or more frozen thresholds above
- **THEN** no new champion is published
- **THEN** forecast endpoint returns `unavailable` or continues prior non-expired champion with explicit policy metadata

### Requirement: Forecast API SHALL return probabilistic horizon-level outputs
The system SHALL expose horizon-level point and interval forecasts with confidence metadata instead of point-only predictions.

#### Scenario: Ready forecast response includes intervals
- **WHEN** champion forecast state is `ready`
- **THEN** response includes `horizon_id`, point estimate, lower bound, upper bound, confidence level, and model snapshot reference
- **THEN** response includes as-of timestamps and training window metadata

#### Scenario: Stale or error states are explicit
- **WHEN** champion snapshot is older than `168` hours without qualified replacement or runtime errors occur
- **THEN** response state is `stale` or `error` with factual reasons
- **THEN** clients are not required to infer lifecycle state from null values

### Requirement: Forecast APIs SHALL remain read-only and non-executional
The system SHALL keep forecasting endpoints read-only and SHALL not emit execution instructions or guaranteed-return claims.

#### Scenario: Forecast request receives non-advice output
- **WHEN** a client requests forecast data
- **THEN** response contains analytical estimates and uncertainty metadata only
- **THEN** no buy, sell, rebalance, or guaranteed-return instruction is produced
