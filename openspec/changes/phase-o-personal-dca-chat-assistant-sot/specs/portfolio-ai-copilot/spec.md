## ADDED Requirements

### Requirement: Copilot SHALL support `dca_assessment` with deterministic DCA SOT policy evaluation
The system SHALL support a dedicated `dca_assessment` operation that applies a deterministic DCA SOT policy pipeline before any AI narration.

#### Scenario: DCA assessment evaluates policy gates in deterministic order
- **WHEN** a request is submitted with `operation=dca_assessment`
- **THEN** the backend evaluates data sufficiency, cadence policy, double-down eligibility, fundamentals proxy, and concentration-risk implications in deterministic order
- **THEN** AI narration is grounded in those deterministic outputs rather than replacing them

#### Scenario: Missing critical context remains explicit
- **WHEN** required context for one policy gate is missing or invalid
- **THEN** response semantics include explicit insufficiency caveats and stable reason metadata
- **THEN** the assistant does not fabricate personal-finance assumptions

### Requirement: Copilot SHALL expose deterministic DCA calculator outputs for planning workflows
The system SHALL provide deterministic calculator outputs for DCA planning and comparison workflows in `dca_assessment` responses.

#### Scenario: Assessment includes scenario-comparison calculator output
- **WHEN** the request asks to compare baseline DCA and 2x drawdown-trigger strategy
- **THEN** the response includes deterministic comparison outputs for allocation impact and average-cost-basis projections
- **THEN** calculations remain bounded to approved read-only datasets and request limits

#### Scenario: Concentration-impact calculator is available for planned additions
- **WHEN** a user asks how planned additions change concentration by symbol or sector
- **THEN** the response includes deterministic concentration-delta outputs derived from current portfolio context
- **THEN** the assistant labels those outputs as informational and non-executing

### Requirement: Copilot SHALL accept typed personal policy context for DCA personalization
The system SHALL accept bounded typed policy-context fields for DCA personalization and SHALL enforce explicit validation behavior.

#### Scenario: Typed policy context is valid and applied
- **WHEN** a request supplies in-range policy context values (for example budget/concentration/review settings)
- **THEN** deterministic DCA assessment uses those values in policy checks and explanation metadata
- **THEN** resulting recommendations remain bounded by read-only and non-advice constraints

#### Scenario: Policy context is invalid or out of range
- **WHEN** a request includes malformed or out-of-range policy context values
- **THEN** the request is rejected with stable blocked/error semantics and reason metadata
- **THEN** no assessment output is generated from invalid policy inputs

### Requirement: Copilot SHALL emit assistant lifecycle and tool-call event metadata
The system SHALL expose bounded event metadata for assistant request lifecycle and tool-call execution so clients can render transparent progress states.

#### Scenario: Successful request emits ordered lifecycle and tool-call events
- **WHEN** one copilot request is processed successfully
- **THEN** the response stream/metadata includes ordered lifecycle events (`start`, `token` optional, `tool_call` optional, `end`)
- **THEN** each emitted `tool_call` event includes stable tool identifiers and bounded metadata

#### Scenario: Failed request emits deterministic failure event
- **WHEN** one copilot request fails due policy, dependency, or provider/runtime errors
- **THEN** the emitted lifecycle includes deterministic failure semantics (`error`) with stable reason metadata
- **THEN** clients can render failure state without parsing provider-specific raw error strings

### Requirement: Copilot SHALL support bounded conversation persistence with evidence-linked replay
The system SHALL support bounded persisted copilot sessions for personal DCA workflows and SHALL preserve evidence references for replayed assistant turns.

#### Scenario: Session replay returns prior messages with evidence continuity
- **WHEN** a user reopens one persisted DCA assistant session
- **THEN** replayed turns include prior assistant/user messages and associated evidence references
- **THEN** replay remains bounded by configured retention and message limits

#### Scenario: Persistence bounds are exceeded
- **WHEN** a session or retention request exceeds configured bounds
- **THEN** the system rejects or truncates with explicit bounded semantics
- **THEN** no silent unbounded retention behavior is introduced

### Requirement: Copilot SHALL include deterministic context-card synthesis for DCA assessments
The system SHALL produce deterministic context-card summaries (gainers/losers and symbol-relevant news summary) for `dca_assessment` responses when source context is available.

#### Scenario: Context cards are available and returned with evidence metadata
- **WHEN** source market/portfolio/news context is available
- **THEN** response includes bounded context-card outputs with explicit source/evidence metadata
- **THEN** cards remain informational and non-executing

#### Scenario: Context card inputs are unavailable
- **WHEN** one or more required inputs for context cards are missing or stale
- **THEN** response includes explicit unavailable/insufficiency card semantics
- **THEN** no fabricated context summary is generated
