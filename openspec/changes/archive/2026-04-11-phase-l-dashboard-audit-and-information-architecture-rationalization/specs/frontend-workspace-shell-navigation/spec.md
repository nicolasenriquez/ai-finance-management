## ADDED Requirements

### Requirement: Workspace shell SHALL support route-aware density modes
The workspace shell SHALL provide route-aware density modes so non-critical chrome can be reduced on high-density analytical routes while preserving orientation and navigation continuity.

#### Scenario: High-density route uses reduced shell chrome
- **WHEN** a user opens a route configured for dense analytical interpretation
- **THEN** optional shell surfaces (for example pulse/auxiliary context blocks) are collapsed or simplified by default
- **THEN** core navigation and trust semantics remain visible and functional

### Requirement: Shell-first viewport SHALL prioritize analytical content over auxiliary chrome
The shell SHALL ensure auxiliary workspace chrome does not dominate first-surface analytical real estate on primary routes.

#### Scenario: First-surface scan remains analysis-first
- **WHEN** one primary route is rendered
- **THEN** the first-surface composition keeps route job context and primary analytical module visually ahead of auxiliary shell cards
- **THEN** users can identify portfolio state intent without scanning multiple shell utility panels first

### Requirement: Shell density choices SHALL remain deterministic and testable by route
Route-level shell density behavior SHALL be deterministic and covered by contract tests to prevent ad-hoc chrome regressions.

#### Scenario: Route shell mode is stable across navigation and reload
- **WHEN** users navigate between routes or reload a route
- **THEN** shell density mode remains consistent with route policy
- **THEN** shell behavior does not drift due to transient client-only state
