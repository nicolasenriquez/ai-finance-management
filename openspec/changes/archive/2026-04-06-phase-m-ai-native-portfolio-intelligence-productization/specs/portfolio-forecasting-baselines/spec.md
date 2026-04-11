## ADDED Requirements

### Requirement: Forecasting baseline policy SHALL include quantile-boosting candidates
The system SHALL support a quantile-boosting candidate family in the approved baseline policy for probabilistic forecast generation.

#### Scenario: Quantile candidate is evaluated alongside approved baselines
- **WHEN** forecast training/evaluation executes for supported scope
- **THEN** quantile-boosting candidates are evaluated with the same policy gates as other approved families
- **THEN** candidate evaluation metadata is persisted for governance audit

#### Scenario: Quantile candidate is policy-disallowed
- **WHEN** policy configuration excludes quantile-boosting family for a scope
- **THEN** the candidate is skipped with explicit policy reason metadata
- **THEN** no hidden candidate execution occurs

### Requirement: Forecast responses SHALL include percentile interval outputs
Forecast responses SHALL include percentile interval outputs (`p10`, `p50`, `p90` or equivalent explicit quantiles) per horizon with confidence semantics.

#### Scenario: Ready forecast response includes percentile bands
- **WHEN** forecast state is `ready`
- **THEN** each horizon includes lower/median/upper quantile values with confidence metadata
- **THEN** clients can render fan-chart interval visuals without inferring missing bounds

#### Scenario: Interval metadata is unavailable
- **WHEN** interval calibration or quantile generation fails policy checks
- **THEN** the response state is explicit (`stale`, `unavailable`, or `error`) with reason metadata
- **THEN** point-only forecasts are not presented as interval-complete outputs

### Requirement: Forecast promotion policy SHALL keep interval-calibration gates explicit
The promotion policy SHALL require interval-calibration and baseline-comparison gates before promoting a quantile forecast champion.

#### Scenario: Candidate fails calibration gate
- **WHEN** candidate interval calibration metrics fail approved thresholds
- **THEN** candidate is not promoted and lifecycle reason metadata records the failed gate
- **THEN** existing non-expired champion remains active when policy allows
