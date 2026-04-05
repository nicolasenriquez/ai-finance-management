# frontend-ai-copilot-workspace Specification

## Purpose
TBD - created by archiving change phase-h-ai-layering-read-only-portfolio-copilot. Update Purpose after archive.
## Requirements
### Requirement: Frontend SHALL expose a dedicated portfolio copilot workspace surface
The frontend SHALL provide a dedicated portfolio copilot surface within the portfolio workspace so AI-assisted analysis is discoverable without overloading existing summary, risk, or report screens.

#### Scenario: User navigates to portfolio copilot
- **WHEN** a user opens the portfolio workspace
- **THEN** the UI exposes a stable entry point for the copilot surface
- **THEN** the copilot route or panel resolves without breaking existing workspace navigation

### Requirement: Copilot surface SHALL render explicit grounded-response states
The frontend SHALL render explicit `idle`, `loading`, `error`, `blocked`, and `ready` states for copilot interactions and SHALL surface evidence and limitation metadata returned by the backend.

#### Scenario: Ready response shows answer, evidence, and limitations
- **WHEN** a copilot response succeeds
- **THEN** the UI displays the assistant answer separately from supporting evidence and limitation messaging
- **THEN** users do not need to infer why the answer was produced or what it excludes

#### Scenario: Blocked or failed response stays explicit
- **WHEN** the backend rejects a request or cannot answer safely
- **THEN** the UI renders a factual blocked or error state with the returned reason
- **THEN** the screen does not present placeholder analysis as if it were valid

#### Scenario: Provider-origin failures map to stable UI reason semantics
- **WHEN** the backend returns normalized reason codes (`rate_limited`, `provider_blocked_policy`, `provider_misconfigured`, `provider_unavailable`)
- **THEN** the UI maps each code to one deterministic blocked/error presentation
- **THEN** raw provider error strings are not required for user-facing state selection

### Requirement: Copilot inputs SHALL keep scope and expectations explicit
The frontend SHALL make the approved v1 copilot boundary visible in the interaction flow, including read-only scope, privacy limitations, and non-advice posture.

#### Scenario: User sees guardrails before asking for help
- **WHEN** the user enters the copilot workflow
- **THEN** the UI presents concise guardrails about read-only behavior, privacy boundary, and non-execution limits
- **THEN** the interaction model does not imply trade execution or hidden data access

### Requirement: Opportunity scan results SHALL separate deterministic candidate data from AI narration
The frontend SHALL present deterministic opportunity-scan outputs and AI narration as distinct UI elements so rule-derived results are inspectable without reading generated prose.

#### Scenario: Opportunity scan shows computed candidates and explanation separately
- **WHEN** an opportunity-scan response is returned
- **THEN** the UI shows the computed candidate list and key rule signals in one stable surface
- **THEN** the AI explanation is rendered separately as interpretive context

### Requirement: Copilot surface SHALL avoid false execution affordances
The frontend SHALL not present buy, sell, rebalance, or order-submission controls within the copilot surface in v1.

#### Scenario: Copilot UI avoids execution controls
- **WHEN** the copilot surface renders analytical answers or opportunity results
- **THEN** it does not display execution controls or automation toggles
- **THEN** users are not misled into thinking the copilot can act on the portfolio directly
