## ADDED Requirements

### Requirement: Portfolio risk estimators SHALL use an approved and pinned quant dependency stack
The system SHALL compute v1 risk estimators using only an approved quant dependency set (`numpy`, `pandas`, `scipy`), with exact dependency pinning in repository manifests/lockfiles to keep outputs reproducible across environments. `pandas-ta` MAY be used for optional analytics overlays but SHALL NOT be the canonical risk-estimator source.

#### Scenario: Runtime estimator dependencies follow approved package policy
- **WHEN** estimator features are built and validated
- **THEN** runtime dependencies used for estimator computation map to the approved package set
- **THEN** rejected packages (`zipline`, `zipline-reloaded`, `pyfolio`, `pyrisk`, `mibian`, `backtrader`, `QuantLib-Python`) are absent from runtime estimator dependency paths in v1

#### Scenario: Quant dependency upgrades require regression evidence
- **WHEN** any approved quant dependency version is changed
- **THEN** estimator regression fixtures are executed for deterministic comparison against baseline outputs
- **THEN** upgrade evidence is recorded in project artifacts before release

### Requirement: Portfolio risk estimators SHALL be computed from persisted truth with explicit formula metadata
The system SHALL compute risk estimators from persisted ledger and persisted market-data history, and each estimator payload SHALL identify calculation metadata such as estimator name, evaluation window, and as-of timestamp.

#### Scenario: Estimator payload includes formula context
- **WHEN** the risk estimator API returns a successful response
- **THEN** each metric includes an explicit identifier and evaluation window context
- **THEN** the response includes an as-of timestamp for the persisted state used in computation

### Requirement: Portfolio risk estimator pipelines SHALL enforce operations-first preprocessing invariants
The system SHALL enforce explicit preprocessing invariants before estimator computation, including sorted timezone-aware series, explicit missing-data handling policy, and explicit frequency/calendar alignment policy.

#### Scenario: Estimator request with invalid preprocessing inputs fails explicitly
- **WHEN** estimator computation inputs violate required preprocessing invariants (for example unsorted index, mixed timezone semantics, or unsupported missing-data coverage)
- **THEN** the API returns an explicit client-facing failure describing the violated invariant
- **THEN** the service does not produce synthetic estimator values from ambiguous preprocessing assumptions

### Requirement: Portfolio risk estimators SHALL publish methodology metadata sufficient for frontend interpretation
The system SHALL include methodology metadata in estimator responses, including estimator identifier, return basis semantics (`simple` or `log`), annualization basis, evaluation window, and as-of timestamp.

#### Scenario: Risk response includes interpretable methodology metadata
- **WHEN** a client requests risk estimators successfully
- **THEN** the response includes methodology metadata fields required by the active estimator contract
- **THEN** frontend clients can display scope and methodology context without inferring hidden defaults

### Requirement: Portfolio risk estimators SHALL follow approved baseline method patterns for v1
The system SHALL implement baseline v1 estimators with approved pandas/NumPy/SciPy patterns and maintain deterministic behavior for default windows `30`, `90`, and `252`.

#### Scenario: Baseline rolling estimators use approved method families
- **WHEN** the service computes baseline volatility, drawdown, or beta-related estimators for supported windows
- **THEN** implementation uses approved method families (for example return derivation via `pct_change`, rolling statistics via `rolling/std` and `rolling/cov/var`, and drawdown via cumulative peak tracking)
- **THEN** outputs match deterministic regression fixtures within declared tolerance bounds

### Requirement: Portfolio risk estimator endpoints SHALL enforce bounded v1 windows
The system SHALL support only the approved v1 estimator windows (`30`, `90`, `252`) unless a later approved capability explicitly expands this set, and SHALL reject unsupported window values explicitly.

#### Scenario: Unsupported risk window is rejected explicitly
- **WHEN** a client requests a risk estimator window outside the approved v1 set
- **THEN** the API returns an explicit client-facing validation failure
- **THEN** the service does not coerce unsupported windows into hidden defaults

### Requirement: SciPy-backed estimator routines SHALL fail explicitly on non-convergence or invalid domains
The system SHALL treat non-convergence and invalid-domain conditions in SciPy-backed routines as explicit failures rather than silently returning fallback estimator values.

#### Scenario: Solver-backed estimator reports non-convergence
- **WHEN** a SciPy-backed estimator routine returns non-converged status or invalid-domain conditions
- **THEN** the API returns an explicit failure with structured reason metadata
- **THEN** no placeholder risk metric is emitted as a successful value

### Requirement: Risk estimators SHALL fail explicitly when required history is insufficient
The system SHALL reject estimator requests that do not meet minimum historical input requirements instead of returning synthetic defaults.

#### Scenario: Insufficient history returns explicit client-facing rejection
- **WHEN** a requested estimator window exceeds available persisted history
- **THEN** the API returns an explicit failure describing insufficient input coverage
- **THEN** the response does not substitute fabricated risk values

### Requirement: Risk estimator endpoints SHALL remain read-only over portfolio and market-data state
Risk estimator execution SHALL not mutate canonical records, ledger events, lots, or persisted market-data rows.

#### Scenario: Estimator request performs no state mutation
- **WHEN** a client requests risk estimator metrics
- **THEN** the service reads persisted state and returns computed metrics
- **THEN** no insert, update, or delete occurs in canonical, ledger, lot, or market-data tables
