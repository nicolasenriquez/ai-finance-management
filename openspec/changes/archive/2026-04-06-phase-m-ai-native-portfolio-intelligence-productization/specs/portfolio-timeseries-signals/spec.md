## ADDED Requirements

### Requirement: Portfolio ML signals SHALL include deterministic behavior-cluster labels
The system SHALL expose deterministic behavior-cluster labels for supported scopes using approved clustering policy inputs and stable label metadata.

#### Scenario: Cluster labels are returned for supported scope
- **WHEN** cluster inputs satisfy minimum history and feature-coverage policy
- **THEN** the response includes stable cluster identifiers/labels for each included symbol
- **THEN** feature provenance metadata is exposed for interpretability

#### Scenario: Cluster inputs are insufficient
- **WHEN** required clustering features are missing or below minimum sample thresholds
- **THEN** the response returns explicit unavailable metadata for clustering outputs
- **THEN** the service does not assign inferred cluster labels

### Requirement: Portfolio ML signals SHALL expose anomaly events with explicit severity metadata
The system SHALL expose anomaly outputs for supported scopes using approved anomaly policy with explicit severity and timestamp metadata.

#### Scenario: Anomaly events are available
- **WHEN** anomaly evaluation succeeds for requested scope/period
- **THEN** response includes anomaly rows with event timestamp, severity, and supporting metric context
- **THEN** lifecycle metadata indicates evaluation freshness and policy version

#### Scenario: Anomaly evaluation fails or is stale
- **WHEN** anomaly evaluation cannot run safely or source inputs are stale beyond policy bounds
- **THEN** response state is explicit (`stale`, `unavailable`, or `error`) with reason metadata
- **THEN** no synthetic anomaly flags are emitted

### Requirement: Clustering and anomaly outputs SHALL remain read-only and reproducible
The system SHALL keep clustering/anomaly generation read-only over persisted data and SHALL return deterministic outputs for equivalent snapshot inputs.

#### Scenario: Equivalent snapshots produce equivalent segmentation/anomaly outputs
- **WHEN** identical scope, snapshot references, and policy parameters are requested
- **THEN** clustering and anomaly payloads are equivalent for the same request shape
- **THEN** no runtime randomness changes output labels or flags
