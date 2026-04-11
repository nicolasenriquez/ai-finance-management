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

### Requirement: Copilot SHALL be reachable from persistent workspace entry points
The frontend SHALL expose the portfolio copilot from a persistent workspace entry point while preserving a dedicated expanded workspace surface for longer analytical sessions.

#### Scenario: User launches copilot without leaving workspace orientation
- **WHEN** a user invokes copilot from the persistent workspace entry point
- **THEN** the copilot opens without breaking the surrounding workspace navigation model
- **THEN** the user can continue into a dedicated expanded copilot surface when more space is required

### Requirement: Copilot presentation SHALL be responsive by device class
The frontend SHALL present copilot in a docked lateral layout on desktop-class viewports and in a full-screen presentation on mobile-class viewports.

#### Scenario: Desktop opens copilot as lateral assistant surface
- **WHEN** a user opens copilot on a desktop-class viewport
- **THEN** the copilot appears as a lateral workspace surface that preserves visibility of surrounding navigation and primary analytical context
- **THEN** the presentation does not force a full-screen route takeover by default

#### Scenario: Desktop user collapses and re-expands copilot panel
- **WHEN** a user collapses the docked desktop copilot panel
- **THEN** the workspace recovers analytical viewport width without losing in-memory copilot conversation state
- **THEN** re-expanding the panel restores the prior composer and response context

#### Scenario: Mobile opens copilot in full-screen mode
- **WHEN** a user opens copilot on a mobile-class viewport
- **THEN** the copilot appears in a full-screen presentation sized for readable conversation, evidence review, and keyboard interaction
- **THEN** the UI does not compress the copilot into a narrow lateral panel on mobile

### Requirement: Copilot launch flow SHALL inherit current analytical context explicitly
The frontend SHALL pass current workspace context such as route, scope, symbol, and period into the copilot launch flow when that context is available and safe to expose.

#### Scenario: Composer reflects invoking route context
- **WHEN** a user opens copilot from an analytical route with active scope selections
- **THEN** the copilot composer shows that scoped context explicitly before request submission
- **THEN** users do not need to restate obvious route context manually to ask a follow-up question

### Requirement: Evidence and limitations SHALL remain inspectable across copilot presentation modes
The frontend SHALL preserve answer, evidence, and limitation visibility when the copilot is shown in persistent or expanded form.

#### Scenario: User expands copilot without losing trust context
- **WHEN** a user moves from a persistent copilot presentation into the expanded copilot surface
- **THEN** the current answer, evidence references, and limitation messaging remain available
- **THEN** the UI does not collapse trust context into hidden or hover-only affordances

### Requirement: Copilot composer SHALL render prompt-suggestion chips for follow-up guidance
The frontend SHALL display a bounded set of prompt-suggestion chips from backend metadata and allow users to apply suggestions into the composer deterministically.

#### Scenario: User applies a suggestion chip to composer draft
- **WHEN** backend response includes prompt suggestions and the user selects one chip
- **THEN** the selected suggestion is inserted into the composer draft using deterministic prefill behavior
- **THEN** the user can edit the draft before submission

#### Scenario: Suggestions remain safe and scoped
- **WHEN** prompt-suggestion chips are rendered
- **THEN** they remain within read-only and non-execution scope messaging
- **THEN** the UI does not present suggestions as guaranteed outcomes

### Requirement: Copilot composer SHALL support attachment references by document ID
The frontend SHALL allow users to attach and remove validated `document_id` references in the copilot composer without introducing raw-file upload behavior in chat routes.

#### Scenario: User adds document reference attachments
- **WHEN** a user selects one or more previously ingested documents for copilot context
- **THEN** the composer displays those attachments as removable document-reference chips
- **THEN** request submission includes only bounded `document_id` references

#### Scenario: Chat route avoids raw-file uploads
- **WHEN** the copilot composer is used in persistent or expanded mode
- **THEN** chat submission uses JSON contracts and not multipart file upload
- **THEN** users are directed to ingestion workflows when a document is not yet available as a reference

### Requirement: Copilot UI SHALL render guided question packs by active decision lens
The frontend SHALL render bounded suggested-question packs that adapt to active lens context (dashboard, risk, rebalancing, holdings, or instrument).

#### Scenario: Suggested questions adapt to lens context
- **WHEN** a user opens copilot from one workspace lens
- **THEN** suggestion chips prioritize relevant prompts for that lens
- **THEN** chips remain editable before submission and stay within read-only boundaries

### Requirement: Copilot UI SHALL present structured response sections explicitly
The frontend SHALL render copilot response sections for `answer`, `evidence`, `assumptions`, `caveats`, and `suggested_follow_ups` as distinct visual modules.

#### Scenario: Structured sections remain visible in docked and expanded modes
- **WHEN** a response is rendered in persistent or expanded copilot views
- **THEN** all structured sections remain inspectable without hidden hover-only access
- **THEN** evidence references remain navigable and keyboard accessible

### Requirement: Copilot workspace SHALL provide what-changed and news-context handoff affordances
The frontend SHALL provide explicit handoff affordances from copilot responses into dashboard what-changed panels and holdings/news context surfaces.

#### Scenario: User navigates from copilot claim to supporting workspace module
- **WHEN** a copilot response references a change driver or news context item
- **THEN** users can open corresponding workspace lens/module via stable navigation affordance
- **THEN** navigation preserves period/scope context where possible

### Requirement: Copilot UI SHALL preserve explicit blocked/unavailable semantics for missing context
The frontend SHALL preserve deterministic blocked/unavailable presentation for missing analytics, ML, or news context dependencies.

#### Scenario: Missing dependency remains explicit
- **WHEN** backend indicates missing dependency for one response section
- **THEN** the UI renders explicit unavailable copy for that section with reason metadata
- **THEN** no placeholder-generated prose is shown as factual completion
