## ADDED Requirements

### Requirement: The frontend reset SHALL archive the pre-redesign UI into `/v0`
Before the active frontend is replaced, the repository SHALL store the current frontend in a recoverable `/v0` archive path so the redesign does not destroy prior work.

#### Scenario: Legacy frontend remains recoverable during the reset
- **WHEN** implementation begins for the compact trading dashboard
- **THEN** the current frontend is moved or copied into a dedicated `/v0` archive location before live replacement work proceeds
- **THEN** the archive includes enough structure or manifest context to understand what was preserved and what was intentionally not carried forward

### Requirement: The redesign SHALL preserve behavior-only assets intentionally
The reset SHALL preserve only explicitly approved high-value behaviors from the current frontend rather than carrying the entire shell and page structure into the rebuilt app.

#### Scenario: Preserve list is explicit and bounded
- **WHEN** the archive and rebuild plan are prepared
- **THEN** the redesign records which current behaviors are kept, moved, or removed
- **THEN** preserved assets are chosen for decision value, not because they already exist
