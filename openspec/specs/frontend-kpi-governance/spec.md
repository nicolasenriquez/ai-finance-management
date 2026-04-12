# frontend-kpi-governance Specification

## Purpose
TBD - created by archiving change phase-f-dashboard-and-quant-ux-hardening. Update Purpose after archive.
## Requirements
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

### Requirement: Promoted analytical KPIs SHALL expose analyst-authored explainability context
The system SHALL define explainability content for promoted analytical KPIs, including plain-language definition, relevance, interpretation guidance, comparison context, and current-context notes where payload data supports it.

#### Scenario: KPI definition explains meaning and relevance
- **WHEN** a KPI is promoted to primary route-level analytical context
- **THEN** the KPI catalog includes a plain-language definition and a `why it matters` explanation
- **THEN** the KPI includes interpretation and comparison guidance so users can understand whether the current reading is good, bad, high, low, or inconclusive
- **THEN** unexplained shorthand labels are avoided or paired with explicit clarification

### Requirement: KPI governance SHALL classify promoted metrics by interpretation tier
The system SHALL classify promoted workspace KPIs as `Core 10` or advanced diagnostics, with explicit route placement and analyst ownership for each promoted metric.

#### Scenario: Promoted KPI includes tier and route ownership
- **WHEN** a KPI is introduced or promoted in the portfolio workspace
- **THEN** the KPI catalog records whether it belongs to the `Core 10` layer or advanced diagnostics
- **THEN** the KPI catalog records the owning route and analyst interpretation boundary before implementation is treated as complete

### Requirement: KPI governance SHALL encode personal-finance decision relevance
The system SHALL document the personal-finance decision value for promoted metrics, including whether a KPI primarily supports allocation review, income monitoring, goal progress, risk posture, or forecast interpretation.

#### Scenario: Personal-finance metrics carry decision tags and interpretation guidance
- **WHEN** a promoted KPI is rendered in the workspace
- **THEN** its governance entry includes personal-finance decision tags and plain-language interpretation guidance
- **THEN** shorthand metrics are not promoted without explanation of why they matter for personal portfolio monitoring
