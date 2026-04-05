## ADDED Requirements

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
