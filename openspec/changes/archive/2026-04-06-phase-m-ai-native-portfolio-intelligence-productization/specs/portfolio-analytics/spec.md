## ADDED Requirements

### Requirement: Portfolio analytics API SHALL expose explicit exposure decomposition datasets
The API SHALL provide exposure decomposition payloads for supported dimensions (`asset_class`, `sector`, `currency`, `country`) with deterministic aggregation and explicit as-of metadata.

#### Scenario: Exposure decomposition returns deterministic grouped outputs
- **WHEN** a client requests exposure decomposition for a supported dimension and scope
- **THEN** the response returns grouped weights and value totals with stable ordering
- **THEN** the payload includes evaluation timestamps and scope metadata for interpretation

#### Scenario: Unsupported decomposition dimension is rejected
- **WHEN** a client requests an unsupported decomposition dimension
- **THEN** the API returns explicit validation failure
- **THEN** no implicit fallback dimension is applied

### Requirement: Portfolio analytics API SHALL expose contribution-to-risk datasets
The API SHALL provide per-symbol contribution-to-risk metrics for supported periods and scopes, with methodology metadata required for chart interpretation.

#### Scenario: Contribution-to-risk payload is returned for supported scope
- **WHEN** contribution-to-risk inputs satisfy minimum history requirements
- **THEN** the response includes per-symbol contribution rows and concentration context
- **THEN** the response includes methodology metadata and as-of references

#### Scenario: Contribution-to-risk inputs are insufficient
- **WHEN** required return history coverage is insufficient for requested scope/period
- **THEN** the API returns explicit unavailable or rejected state with factual coverage reason
- **THEN** the service does not emit synthetic contribution-to-risk values

### Requirement: Portfolio analytics API SHALL expose bounded correlation matrix contracts
The API SHALL provide bounded correlation matrix outputs for supported scopes with explicit minimum-history and symbol-universe policies.

#### Scenario: Correlation matrix is available
- **WHEN** requested scope has sufficient aligned return history for selected symbols
- **THEN** the response includes matrix cells and symbol ordering metadata
- **THEN** the payload includes guardrail metadata for low-sample or partially missing cells

#### Scenario: Correlation matrix cannot be computed safely
- **WHEN** symbol alignment or sample size fails minimum requirements
- **THEN** the API returns explicit failure/unavailable metadata
- **THEN** the service does not backfill guessed correlation values
