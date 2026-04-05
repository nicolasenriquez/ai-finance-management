## ADDED Requirements

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
