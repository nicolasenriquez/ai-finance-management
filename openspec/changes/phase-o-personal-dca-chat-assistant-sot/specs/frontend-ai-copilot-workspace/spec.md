## ADDED Requirements

### Requirement: Copilot composer SHALL expose dedicated `dca_assessment` controls
The frontend SHALL expose a dedicated `dca_assessment` mode with explicit policy-context controls for personal DCA guidance.

#### Scenario: User selects `dca_assessment` and sees policy controls
- **WHEN** the active operation is `dca_assessment`
- **THEN** the composer renders bounded inputs for DCA policy context and strategy settings
- **THEN** the UI makes clear which fields are optional vs required for specific assessment workflows

#### Scenario: Non-DCA operations preserve compact controls
- **WHEN** the active operation is `chat` or `opportunity_scan`
- **THEN** `dca_assessment`-specific policy controls remain hidden
- **THEN** the composer avoids unnecessary density outside DCA-personal workflows

### Requirement: Copilot workspace SHALL render deterministic calculator outputs as first-class assistant surfaces
The frontend SHALL render calculator outputs as explicit deterministic result modules separate from narrative chat text.

#### Scenario: Calculator outputs are visually separated from narration
- **WHEN** `dca_assessment` response includes calculator outputs
- **THEN** UI displays them in dedicated modules with labels for metric meaning, units, and provenance
- **THEN** users can inspect deterministic outputs without parsing markdown narrative only

#### Scenario: Calculator unavailability remains explicit
- **WHEN** one or more calculator outputs cannot be produced due missing context
- **THEN** the workspace renders explicit unavailable/insufficient state copy for those modules
- **THEN** no placeholder numeric values are shown as factual results

### Requirement: Copilot UI SHALL expose lifecycle and tool-event transparency
The frontend SHALL render lifecycle and tool-event traces for assistant requests to improve trust and inspectability.

#### Scenario: Request lifecycle is visible during response generation
- **WHEN** one request is submitted
- **THEN** the UI shows explicit lifecycle progression (`start`, in-flight updates, `end` or failure)
- **THEN** users are not required to infer progress from partial text alone

#### Scenario: Tool usage trace is available when calculators/tools execute
- **WHEN** a response uses one or more deterministic tools
- **THEN** the UI renders a concise tool-event trace with stable tool identifiers
- **THEN** trace visibility remains available in docked and expanded copilot views

### Requirement: Copilot workspace SHALL support persisted-session replay for DCA continuity
The frontend SHALL provide bounded session replay so users can continue prior personal DCA assessments with preserved context and evidence links.

#### Scenario: User reopens prior DCA session
- **WHEN** a user selects one saved DCA assistant session
- **THEN** the workspace restores conversation turns, mode, and associated evidence context
- **THEN** replayed content is visually separated from new in-flight assistant events

#### Scenario: Session replay cannot load
- **WHEN** a persisted session is unavailable, expired, or invalid
- **THEN** the UI presents explicit unavailability messaging and recovery actions
- **THEN** the workspace does not silently open an empty chat as if replay succeeded

### Requirement: Copilot workspace SHALL render deterministic context-card modules
The frontend SHALL display deterministic context-card modules for DCA assessments, including gainers/losers and symbol-relevant news summaries when available.

#### Scenario: Context cards render with evidence and freshness cues
- **WHEN** a `dca_assessment` response includes context-card outputs
- **THEN** cards display values plus evidence/freshness cues and explicit informational framing
- **THEN** cards avoid execution affordances or advice-like CTA language

#### Scenario: Context card data is unavailable
- **WHEN** context-card output is marked unavailable or insufficient
- **THEN** cards render explicit unavailable state messaging with reason cues
- **THEN** no placeholder pseudo-data is rendered

### Requirement: Personal assistant presentation SHALL preserve continuity across docked and expanded usage
The frontend SHALL preserve conversation, calculator outputs, and caveat context across docked panel, expanded route, and mobile full-screen presentations.

#### Scenario: User transitions from docked to expanded view
- **WHEN** a user opens expanded copilot after interacting in docked mode
- **THEN** conversation history, calculator outputs, and caveat/evidence context remain available
- **THEN** operation mode and policy-control selections are preserved unless user explicitly resets them

#### Scenario: Mobile full-screen remains functionally complete
- **WHEN** the assistant is opened on mobile viewport
- **THEN** chat, policy controls, and calculator outputs remain accessible in full-screen layout
- **THEN** core DCA assessment functionality is not reduced to read-only narrative text
