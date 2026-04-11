## ADDED Requirements

### Requirement: Copilot composer SHALL expose DCA controls for opportunity-scan requests
The frontend SHALL render editable DCA controls in the copilot composer when `operation=opportunity_scan` so users can review and adjust strategy profile, drawdown threshold, and multiplier before submission.

#### Scenario: Opportunity-scan mode reveals DCA controls
- **WHEN** the user selects `opportunity_scan` operation
- **THEN** the composer displays DCA control inputs with bounded validation-friendly affordances
- **THEN** control values are presented as explicit request policy, not hidden defaults

#### Scenario: Chat mode hides DCA control surface
- **WHEN** the user selects `chat` operation
- **THEN** DCA-specific controls are hidden to preserve chat composer clarity
- **THEN** the UI does not imply DCA policy adjustments apply to non-opportunity requests

### Requirement: Copilot submit flow SHALL propagate selected DCA controls through typed request payloads
The frontend SHALL send currently selected DCA control values through the typed copilot request contract for opportunity scans, with schema-parity validation behavior across frontend and backend boundaries.

#### Scenario: User submits customized DCA policy inputs
- **WHEN** the user changes threshold or multiplier values and submits an opportunity-scan request
- **THEN** the request payload includes those selected values in `double_down_threshold_pct` and `double_down_multiplier`
- **THEN** the payload remains compatible with existing bounded request constraints

### Requirement: Recommendation bubbles SHALL remain operation-aware and portfolio-business informative
The frontend SHALL render recommendation bubbles using operation-specific catalogs that prioritize portfolio-governance, benchmark context, concentration, drawdown, and capital-deployment framing.

#### Scenario: Chat operation renders business-grade portfolio prompts
- **WHEN** the active operation is `chat`
- **THEN** recommendation bubbles emphasize portfolio monitoring, benchmark-relative interpretation, and risk-governance questions
- **THEN** bubbles avoid low-signal generic prompts that are detached from portfolio context

#### Scenario: Opportunity-scan operation renders DCA-governance prompts
- **WHEN** the active operation is `opportunity_scan`
- **THEN** recommendation bubbles emphasize DCA allocation prioritization, concentration impact, and risk-control trade-offs
- **THEN** bubble copy remains informational and non-executing within read-only copilot boundaries
