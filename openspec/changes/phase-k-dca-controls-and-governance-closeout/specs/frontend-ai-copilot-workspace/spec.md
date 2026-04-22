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

### Requirement: Copilot workspace SHALL render SOT DCA assessment cues for opportunity workflows
The frontend SHALL make SOT DCA interpretation cues visible in opportunity workflows so users can distinguish deterministic classification from interpretive assistant commentary.

#### Scenario: Opportunity response surfaces deterministic vs interpretive layers
- **WHEN** an `opportunity_scan` response is rendered
- **THEN** the workspace exposes deterministic candidate/action-state evidence separately from narrative explanation
- **THEN** the UI keeps fundamentals-proxy caveat and non-advice posture visible in the evidence/limitations surface

#### Scenario: Follow-up prompts map to SOT DCA categories
- **WHEN** recommendation bubbles are rendered for `opportunity_scan`
- **THEN** prompts map to DCA categories such as cadence discipline, concentration impact, hold-off risk, and monitoring cadence
- **THEN** prompts avoid execution language or guaranteed-outcome framing

### Requirement: Copilot presentation SHALL preserve lifecycle transparency across docked and expanded surfaces
The frontend SHALL keep copilot lifecycle state explicit across docked, expanded, and mobile modes so users can audit request progress and trust boundaries.

#### Scenario: Lifecycle state remains explicit during request processing
- **WHEN** a copilot request is submitted from any presentation mode
- **THEN** the UI shows deterministic lifecycle states for request start, in-flight processing, and completion/error outcomes
- **THEN** users are not forced to infer status from partial response text

#### Scenario: Presentation changes do not lose trust context
- **WHEN** a user moves between docked and expanded copilot surfaces
- **THEN** current answer, evidence, caveats, and state monitor context remain available
- **THEN** state continuity is preserved without silently resetting DCA control selections
