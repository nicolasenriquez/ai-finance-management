# portfolio-ai-copilot Specification

## Purpose
TBD - created by archiving change phase-h-ai-layering-read-only-portfolio-copilot. Update Purpose after archive.
## Requirements
### Requirement: Portfolio AI copilot SHALL remain grounded in approved read-only portfolio tools
The system SHALL answer portfolio copilot requests only through an allowlisted set of read-only portfolio-analysis tools backed by approved aggregated contracts, and SHALL not bypass those boundaries with direct database or raw-record access.

#### Scenario: Copilot uses only approved aggregated tools
- **WHEN** a user asks the copilot to explain portfolio movement, performance context, or current portfolio structure
- **THEN** the backend uses only approved read-only tool calls backed by aggregated portfolio contracts
- **THEN** the request path does not execute direct SQL, rebuild ledger state, or read raw canonical PDF payloads

#### Scenario: Allowlist is frozen to audited v1 tool IDs
- **WHEN** the v1 tool registry is loaded
- **THEN** it includes only `portfolio_summary`, `portfolio_time_series`, `portfolio_contribution`, `portfolio_risk_estimators`, `portfolio_risk_evolution`, `portfolio_return_distribution`, `portfolio_hierarchy`, `portfolio_monte_carlo`, `portfolio_health_synthesis`, and `portfolio_quant_metrics`
- **THEN** it excludes lot-detail, raw transaction-event list, quant-report artifact HTML, raw canonical payloads, and any direct SQL access path

#### Scenario: Required tool context is unavailable
- **WHEN** the copilot cannot retrieve the approved tool context needed to answer safely
- **THEN** the response states the missing context explicitly
- **THEN** the assistant does not fabricate unsupported portfolio facts

### Requirement: Portfolio AI copilot SHALL enforce privacy-minimized model context
The system SHALL limit model-visible context to approved aggregated or explicitly redacted portfolio data and SHALL exclude raw private records from prompt assembly.

#### Scenario: Raw record payloads are excluded from model context
- **WHEN** the backend assembles model context for a copilot request
- **THEN** raw canonical document payloads, unbounded transaction detail, and non-approved private fields are excluded
- **THEN** only approved aggregated, redacted, or already-public context is sent to the model

### Requirement: Portfolio AI copilot SHALL return typed grounded responses with explicit limitations
The system SHALL return structured copilot responses that distinguish answer text from supporting evidence and limitation metadata, and SHALL expose one explicit response state (`ready`, `blocked`, or `error`) so clients do not infer unsupported certainty.

#### Scenario: Successful answer includes evidence and limitations
- **WHEN** the copilot returns a successful answer
- **THEN** the payload includes assistant content plus structured evidence references to the metrics or tools used
- **THEN** the response includes explicit limitation and non-advice messaging

#### Scenario: Blocked or error answer carries stable reason code
- **WHEN** the copilot cannot safely answer or the provider/runtime fails
- **THEN** the payload sets response state to `blocked` or `error`
- **THEN** the payload includes one stable machine-readable reason code

#### Scenario: Request bounds are enforced before orchestration
- **WHEN** a request exceeds max prior turns (`8`), max user message length (`2000` chars), or max tool budget (`6`)
- **THEN** the backend rejects the request with explicit blocked/error semantics
- **THEN** no provider call is attempted for invalid request shape

### Requirement: Portfolio AI copilot SHALL use one frozen Groq provider adapter contract in v1
The system SHALL call exactly one Groq OpenAI-compatible chat-completions adapter contract with no fallback provider, one configured model allowlist, and explicit adapter-parameter validation.

#### Scenario: Provider call uses frozen adapter contract
- **WHEN** the copilot invokes the model provider
- **THEN** it uses the frozen Groq chat-completions adapter contract with one configured model from the allowlist
- **THEN** unsupported adapter parameters are rejected explicitly before provider invocation
- **THEN** the backend does not switch to a fallback provider

#### Scenario: Provider contract is sourced from explicit v1 config keys
- **WHEN** the backend initializes provider configuration
- **THEN** it requires `GROQ_API_KEY`, `PORTFOLIO_AI_COPILOT_MODEL`, and `PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST`
- **THEN** timeout/retry behavior is read from explicit copilot config keys rather than hidden defaults

### Requirement: Portfolio AI copilot SHALL normalize provider failures into stable reason codes
The system SHALL normalize provider/runtime failures to one stable reason code set so frontend blocked/error states remain deterministic across provider message variations.

#### Scenario: Provider failure is normalized
- **WHEN** the provider returns a rate-limit, policy/permission block, misconfiguration response, or upstream unavailability
- **THEN** the response reason code is normalized to one of `rate_limited`, `provider_blocked_policy`, `provider_misconfigured`, or `provider_unavailable`
- **THEN** the UI contract does not depend on raw provider error strings

### Requirement: Opportunity scan SHALL separate deterministic scoring from AI narration
The system SHALL compute candidate additions, watchlist opportunities, or "discount" suggestions from explicit deterministic rules first and SHALL use AI only to explain those deterministic results.

#### Scenario: Opportunity candidates are ranked by rules before narration
- **WHEN** a user requests candidate additions or discounted opportunities
- **THEN** the backend computes candidate eligibility and ranking from explicit deterministic rules over approved portfolio and market context
- **THEN** the AI response explains the computed result instead of inventing opaque selection logic

#### Scenario: Opportunity ranking uses the frozen deterministic score formula
- **WHEN** eligible candidates have required input history
- **THEN** the ranking score is computed as `0.45 * discount_score + 0.35 * momentum_score + 0.20 * stability_score`
- **THEN** tie-breakers are deterministic and stable for equal-state replays

#### Scenario: Opportunity scan fails explicitly when rule inputs are incomplete
- **WHEN** required inputs for deterministic opportunity scoring are unavailable or insufficient
- **THEN** the system returns an explicit unavailable or rejected state with the factual reason
- **THEN** no candidate ranking is fabricated from partial context

### Requirement: Portfolio AI copilot SHALL reject non-read-only or unsafe requests explicitly
The system SHALL reject or reframe requests that cross the approved v1 AI boundary, including trade execution, guaranteed-return claims, or disclosure of raw private data.

#### Scenario: User asks for execution or guaranteed advice
- **WHEN** a user asks the copilot to buy, sell, rebalance automatically, or guarantee a return outcome
- **THEN** the system responds with explicit boundary messaging
- **THEN** no execution side effect or prescriptive trade instruction is produced

### Requirement: Portfolio AI copilot SHALL remain stateless and bounded in v1
The system SHALL process copilot interactions from bounded request-supplied conversation history and SHALL not require server-side chat memory, vector retrieval, or persistent conversation state in v1.

#### Scenario: Bounded conversation history is processed without server memory
- **WHEN** a client submits a copilot request with prior conversation turns
- **THEN** the backend processes only the supplied bounded history for that request (maximum `8` prior turns)
- **THEN** the request enforces maximum user-input length (`2000` characters)
- **THEN** the request enforces maximum tool invocations (`6`) for one response cycle
- **THEN** the request does not depend on server-side chat-memory persistence to succeed

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

### Requirement: Copilot responses SHALL follow one structured decision-narrative envelope
The system SHALL return copilot answers using structured fields `answer`, `evidence`, `assumptions`, `caveats`, and `suggested_follow_ups` so users can distinguish factual grounding from interpretation.

#### Scenario: Ready response includes all narrative envelope sections
- **WHEN** copilot returns state `ready`
- **THEN** the payload includes structured narrative sections and stable evidence references
- **THEN** omissions in assumptions/caveats are explicit rather than implied

#### Scenario: Blocked or unavailable response remains structured
- **WHEN** copilot cannot safely answer due missing context or policy boundary
- **THEN** the response uses blocked/unavailable semantics and still returns structured caveat messaging
- **THEN** clients do not infer validity from free-form text shape

### Requirement: Copilot SHALL provide grounded question-pack guidance for high-value workflows
The system SHALL expose bounded suggested-question packs for high-value workflows such as performance attribution, concentration risk, volatility drivers, and scenario/rebalancing interpretation.

#### Scenario: Suggested questions are workflow-specific
- **WHEN** a user opens copilot with route/scope context
- **THEN** suggestion payloads include route-relevant prompts (for example "why is my portfolio down today?")
- **THEN** suggestions remain within read-only, non-execution boundaries

#### Scenario: Suggestion context is insufficient
- **WHEN** required route/scope context is unavailable
- **THEN** the suggestion pack degrades to a safe default question set with explicit context caveat
- **THEN** no fabricated symbol-specific prompt is produced

### Requirement: Copilot SHALL compose what-changed explanations from typed internal tools
The system SHALL produce "what changed" narratives using approved typed analytics/ML/news tools and SHALL expose tool-evidence linkage for each claim.

#### Scenario: What-changed answer contains traceable claims
- **WHEN** a user requests period-over-period change explanation
- **THEN** each key claim links to evidence entries with tool identifiers and as-of references
- **THEN** the answer includes assumptions and caveats for incomplete coverage

#### Scenario: Required what-changed evidence is unavailable
- **WHEN** one or more required tools are unavailable or stale
- **THEN** copilot returns partial or blocked explanation state with explicit missing-tool reasons
- **THEN** the assistant does not fill gaps with unsupported claims
