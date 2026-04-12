## ADDED Requirements

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
