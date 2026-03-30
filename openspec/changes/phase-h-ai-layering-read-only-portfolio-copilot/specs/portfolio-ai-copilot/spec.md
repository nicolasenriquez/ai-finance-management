## ADDED Requirements

### Requirement: Portfolio AI copilot SHALL remain grounded in approved read-only portfolio tools
The system SHALL answer portfolio copilot requests only through an allowlisted set of read-only portfolio-analysis tools backed by approved aggregated contracts, and SHALL not bypass those boundaries with direct database or raw-record access.

#### Scenario: Copilot uses only approved aggregated tools
- **WHEN** a user asks the copilot to explain portfolio movement, performance context, or current portfolio structure
- **THEN** the backend uses only approved read-only tool calls backed by aggregated portfolio contracts
- **THEN** the request path does not execute direct SQL, rebuild ledger state, or read raw canonical PDF payloads

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
The system SHALL return structured copilot responses that distinguish answer text from supporting evidence and limitation metadata so clients do not infer unsupported certainty.

#### Scenario: Successful answer includes evidence and limitations
- **WHEN** the copilot returns a successful answer
- **THEN** the payload includes assistant content plus structured evidence references to the metrics or tools used
- **THEN** the response includes explicit limitation and non-advice messaging

### Requirement: Opportunity scan SHALL separate deterministic scoring from AI narration
The system SHALL compute candidate additions, watchlist opportunities, or "discount" suggestions from explicit deterministic rules first and SHALL use AI only to explain those deterministic results.

#### Scenario: Opportunity candidates are ranked by rules before narration
- **WHEN** a user requests candidate additions or discounted opportunities
- **THEN** the backend computes candidate eligibility and ranking from explicit deterministic rules over approved portfolio and market context
- **THEN** the AI response explains the computed result instead of inventing opaque selection logic

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
- **THEN** the backend processes only the supplied bounded history for that request
- **THEN** the request does not depend on server-side chat-memory persistence to succeed
