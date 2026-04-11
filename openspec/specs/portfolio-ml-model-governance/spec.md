# portfolio-ml-model-governance Specification

## Purpose
TBD - created by archiving change phase-i-ml-timeseries-signal-and-forecasting. Update Purpose after archive.
## Requirements
### Requirement: Model governance SHALL persist auditable snapshot metadata
The system SHALL persist model-run snapshots with reproducibility and policy metadata sufficient for audit and rollback decisions.

#### Scenario: Snapshot metadata is recorded for completed run
- **WHEN** training/evaluation run completes
- **THEN** snapshot metadata includes model family, feature-set hash, data window boundaries, metric vector, baseline comparator metrics, run timestamp, and expiry timestamp
- **THEN** snapshot metadata includes run status and failure reason fields when applicable

### Requirement: Governance SHALL manage champion lifecycle deterministically
The system SHALL track candidate and champion states with deterministic promotion, retention, and expiry rules.

#### Scenario: Champion promotion archives prior champion
- **WHEN** a new snapshot satisfies promotion policy
- **THEN** system marks it as champion and archives prior champion state with replacement metadata
- **THEN** exactly one active champion exists per scope and forecast family

#### Scenario: Expired champion is not treated as ready
- **WHEN** active champion passes expiry policy without replacement
- **THEN** endpoint lifecycle state is `stale` or `unavailable` based on policy
- **THEN** consumers receive explicit expiry reason metadata

### Requirement: Governance SHALL expose read-only registry audit contract
The system SHALL provide read-only registry retrieval for model snapshots and promotion decisions.

#### Scenario: Registry query returns decision lineage
- **WHEN** client requests model registry history
- **THEN** response includes snapshot lineage, promotion outcomes, policy thresholds, and as-of timestamps
- **THEN** response supports filtering by scope, model family, and lifecycle state

#### Scenario: Registry contract uses shared lifecycle envelope
- **WHEN** `GET /api/portfolio/ml/registry` is requested
- **THEN** response includes `state` in `ready|unavailable|stale|error`
- **THEN** response includes `state_reason_code`, `state_reason_detail`, and evaluation/as-of timestamps aligned to signals/forecast contracts

### Requirement: Governance SHALL enforce v1 allowed-model policy
The system SHALL reject unsupported model families in v1 by explicit policy, including deep-learning and Prophet-class requests.

#### Scenario: Unsupported model request is rejected
- **WHEN** a training request targets disallowed family such as LSTM, generic RNN, Prophet, or non-portfolio clustering
- **THEN** the system rejects the request with `unsupported_model_policy` reason
- **THEN** no registry snapshot is promoted from the rejected request

### Requirement: Governance SHALL track segmentation and anomaly model families explicitly
The model registry SHALL support explicit lifecycle tracking for clustering and anomaly model families in addition to forecasting families.

#### Scenario: Registry records segmentation/anomaly lineage
- **WHEN** clustering or anomaly evaluation runs complete
- **THEN** registry entries include model family, feature policy metadata, lifecycle state, and evaluation timestamps
- **THEN** lineage is queryable by scope and family type

### Requirement: Governance SHALL enforce family-specific promotion and freshness policy
The system SHALL enforce family-specific promotion and freshness rules for forecasting, clustering, and anomaly outputs.

#### Scenario: Family-specific stale state is surfaced
- **WHEN** an active family output exceeds freshness policy without replacement
- **THEN** registry and serving contracts expose `stale`/`unavailable` with family-specific reason codes
- **THEN** consumers are not forced to infer family health from missing rows

### Requirement: Governance SHALL expose auditability for feature-set and policy versions
The model registry SHALL expose feature-set hash/version and policy version metadata for every promoted family output.

#### Scenario: Registry response includes reproducibility metadata
- **WHEN** a client requests governance history for one scope/family
- **THEN** response includes feature-set and policy version metadata for promoted and rejected candidates
- **THEN** rollback and audit workflows can identify why one candidate was selected
