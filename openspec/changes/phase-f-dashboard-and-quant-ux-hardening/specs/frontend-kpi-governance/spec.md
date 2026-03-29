## ADDED Requirements

### Requirement: Portfolio workspace KPI catalog SHALL be analyst-owned and route-scoped
The system SHALL maintain a documented KPI catalog owned by a named analyst role that defines metric purpose, formula narrative, and required route placement for `Home`, `Analytics`, `Risk`, and `Quant/Reports`.

#### Scenario: KPI placement contract is explicit before implementation
- **WHEN** frontend modules are planned or modified for workspace routes
- **THEN** each KPI referenced by those modules maps to one route owner in the KPI catalog
- **THEN** KPI narrative and formula context are documented before implementation tasks are marked ready

### Requirement: KPI placement changes SHALL remain traceable and deterministic
The repository SHALL record KPI placement changes with explicit rationale and validation evidence so dashboard information architecture changes remain auditable.

#### Scenario: KPI placement update includes rationale and evidence
- **WHEN** a KPI is moved between workspace routes
- **THEN** the change artifact includes an explicit reason for the move and the intended analyst interpretation boundary
- **THEN** linked validation evidence is recorded in release documentation and changelog entries
