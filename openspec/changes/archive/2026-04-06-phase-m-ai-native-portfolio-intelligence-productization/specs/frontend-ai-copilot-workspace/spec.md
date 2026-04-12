## ADDED Requirements

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
