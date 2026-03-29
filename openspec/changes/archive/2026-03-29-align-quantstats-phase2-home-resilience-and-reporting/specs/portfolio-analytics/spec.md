## ADDED Requirements

### Requirement: Quant metrics endpoint SHALL be version-compatible with pinned QuantStats API surface
The system SHALL compute QuantStats-backed metrics through an explicit adapter contract that matches the pinned runtime QuantStats API surface, and SHALL fail explicitly when adapter compatibility checks detect unsupported call paths.

#### Scenario: Adapter-compatible metrics are returned successfully
- **WHEN** a client requests quant metrics for a supported period and adapter compatibility checks pass
- **THEN** the endpoint returns deterministic metric rows with display metadata
- **THEN** returned metrics are derived from persisted portfolio and market history only

#### Scenario: Adapter compatibility mismatch is rejected explicitly
- **WHEN** required QuantStats call paths are unavailable for the pinned runtime version
- **THEN** the endpoint returns explicit failure with factual compatibility detail
- **THEN** the service does not fabricate substitute metric values

### Requirement: Benchmark-relative quant metrics SHALL be optional and explicit
The quant metrics endpoint SHALL treat benchmark-relative metrics as optional outputs that are emitted only when compatible benchmark series and adapter call paths are available; absence SHALL be explicit and SHALL NOT invalidate core quant metric computation.

#### Scenario: Benchmark-relative metrics omitted without blocking core metrics
- **WHEN** benchmark-relative metrics cannot be computed safely for the selected period
- **THEN** the endpoint still returns supported non-benchmark quant metrics
- **THEN** the payload includes explicit benchmark-context metadata indicating omission reason/scope

### Requirement: Quant metrics endpoint SHALL remain read-only and deterministic
Quant metric requests SHALL remain read-only over canonical, ledger, lot, and market-data state and SHALL preserve deterministic ordering and period semantics.

#### Scenario: Quant metrics request produces deterministic read-only output
- **WHEN** the same persisted state and period are requested repeatedly
- **THEN** metric ordering and value semantics remain deterministic for the same inputs
- **THEN** the request path performs no database mutation side effects
