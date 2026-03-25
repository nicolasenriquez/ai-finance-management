## ADDED Requirements

### Requirement: Market-data operations SHALL define one approved operational smoke and blocker-evidence workflow
The system SHALL define one operator-facing workflow for `market-refresh-yfinance` and one for `data-sync-local` that specifies how success evidence, failure evidence, and blocker follow-up are recorded for the current local-first Phase 6 posture.

#### Scenario: Operator records successful refresh evidence
- **WHEN** an operator runs the approved market-data refresh workflow successfully
- **THEN** the workflow yields explicit evidence of the command invoked, requested scope, provider identity, and resulting snapshot provenance
- **THEN** the runbook identifies that evidence as sufficient for current operational smoke validation

#### Scenario: Operator records blocked refresh evidence
- **WHEN** an operator runs the approved market-data refresh workflow and the provider, network, or runtime environment prevents safe completion
- **THEN** the workflow yields explicit blocker evidence identifying the failing stage and rejection reason
- **THEN** the runbook requires that blocked outcome to be recorded instead of treating the smoke run as implicitly complete

### Requirement: Market-data operations SHALL remain schedule-ready through existing local command surfaces
The system SHALL keep the current market-data refresh and combined local sync workflows callable through the existing command surfaces in a way that future scheduler automation can invoke without redefining refresh semantics.

#### Scenario: Future scheduler reuses the current invocation contract
- **WHEN** a future automation mechanism needs to trigger the approved market-data refresh workflow
- **THEN** it can invoke the existing local command surface without requiring a second refresh contract
- **THEN** the refresh semantics, fail-fast behavior, and evidence expectations remain the same as the manual operator path

#### Scenario: Scheduling infrastructure remains out of scope for this slice
- **WHEN** the current change defines schedule-ready posture
- **THEN** it documents invocation expectations and operator prerequisites on top of the existing command surfaces
- **THEN** it does not require cron, queue, worker, or public API infrastructure to satisfy the current operational contract
