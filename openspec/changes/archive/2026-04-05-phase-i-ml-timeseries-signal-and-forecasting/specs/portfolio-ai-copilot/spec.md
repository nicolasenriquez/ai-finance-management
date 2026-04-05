## ADDED Requirements

### Requirement: Copilot SHALL expose phase-i ML outputs through allowlisted read-only tools
The system SHALL make phase-i signal, CAPM, forecast, and model-governance outputs available to copilot only through typed allowlisted tools with explicit evidence metadata.

#### Scenario: Copilot answer includes evidence for `portfolio_ml` tools
- **WHEN** a user asks a question that requires phase-i ML outputs
- **THEN** the copilot orchestrator uses only approved read-only `portfolio_ml` tool adapters
- **THEN** the response evidence payload includes stable tool identifiers and provenance references for the used ML outputs

#### Scenario: Missing phase-i ML context fails explicitly
- **WHEN** required phase-i ML data is unavailable, stale beyond policy, or not yet promoted
- **THEN** copilot returns explicit blocked or error semantics with a stable reason code
- **THEN** the assistant does not fabricate forecast or CAPM claims from partial context

### Requirement: Copilot SQL analytics SHALL be governed by read-only allowlisted templates
The system SHALL support copilot SQL analytics through typed template IDs and validated parameters only, and SHALL prohibit free-form SQL text execution.

#### Scenario: Allowed SQL template executes within policy bounds
- **WHEN** copilot selects a supported SQL template ID with valid parameters
- **THEN** execution runs in read-only mode with configured row-budget and timeout limits
- **THEN** response metadata includes template ID, bounded row count, and execution audit identifiers

#### Scenario: Free-form or unsupported SQL request is rejected
- **WHEN** copilot receives raw SQL text or an unapproved template ID
- **THEN** the request is rejected explicitly with stable policy reason semantics
- **THEN** no SQL statement is executed

### Requirement: Copilot chat SHALL accept attachments by document reference, not raw file bytes
The system SHALL allow copilot requests to reference previously ingested documents using bounded `document_id` values and SHALL not accept multipart file uploads on the chat endpoint.

#### Scenario: Valid document references are accepted
- **WHEN** a chat request includes one or more valid `document_id` references from prior ingestion
- **THEN** the backend validates those IDs and includes only approved derived context in prompt assembly
- **THEN** raw document payloads are not forwarded directly to the model provider

#### Scenario: Invalid document reference fails fast
- **WHEN** a chat request includes an unresolved or unauthorized `document_id`
- **THEN** the request is rejected with explicit blocked/error semantics and factual reason metadata
- **THEN** no provider call is attempted

### Requirement: Copilot responses SHALL include optional prompt-suggestion metadata
The system SHALL expose optional prompt suggestions in copilot responses so clients can render recommendation chips for next-question guidance.

#### Scenario: Response includes bounded suggestion list
- **WHEN** copilot returns `ready` or `blocked` state with enough context to guide follow-up
- **THEN** the payload may include a bounded list of concise suggestion prompts
- **THEN** suggestions stay within read-only and non-execution boundaries

#### Scenario: Suggestion generation failure does not mask main response
- **WHEN** suggestion generation fails or has insufficient context
- **THEN** the primary copilot response state and content remain valid without suggestions
- **THEN** clients are not forced to infer response validity from suggestion availability
