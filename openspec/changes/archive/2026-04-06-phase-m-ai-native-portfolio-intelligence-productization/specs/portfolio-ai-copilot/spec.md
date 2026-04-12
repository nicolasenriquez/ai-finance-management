## ADDED Requirements

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
