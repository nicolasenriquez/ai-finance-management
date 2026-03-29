## ADDED Requirements

### Requirement: Frontend release readiness SHALL include chart-consistency verification across workspace routes
Frontend release validation SHALL include deterministic checks that chart container sizing, spacing tokens, and shared header semantics remain consistent across `Home`, `Analytics`, and `Risk` route modules.

#### Scenario: Chart composition evidence is captured before release sign-off
- **WHEN** release readiness validation is executed for workspace routes
- **THEN** evidence confirms chart modules use approved shared composition contracts across routes
- **THEN** regressions in spacing, container sizing, or duplicated chart layout patterns fail release readiness gates

### Requirement: Frontend release readiness SHALL validate dedicated Quant/Reports workflow states
Frontend release validation SHALL verify explicit loading, error, unavailable, and ready states for the dedicated Quant/Reports report workflow, including route-level accessibility and retry determinism.

#### Scenario: Quant/Reports states are explicit and keyboard-accessible
- **WHEN** report generation or retrieval succeeds, fails, or returns unavailable state
- **THEN** the dedicated Quant/Reports surface renders explicit state messaging and deterministic retry behavior
- **THEN** keyboard-only flows can trigger and inspect report lifecycle states without hidden controls
