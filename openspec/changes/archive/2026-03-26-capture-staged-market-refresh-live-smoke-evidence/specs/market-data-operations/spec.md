## MODIFIED Requirements

### Requirement: Market-data operations SHALL define one approved operational smoke and blocker-evidence workflow
The system SHALL define one operator-facing workflow for `market-refresh-yfinance` and one for `data-sync-local` that specifies how fresh staged live-smoke evidence is captured for the current local-first Phase 6 posture, including the required standalone refresh sequence (`core`, then `100`), one follow-on combined sync run, and how success, failure, and blocker follow-up are recorded.

#### Scenario: Operator records fresh staged refresh evidence
- **WHEN** an operator performs the approved live smoke workflow after market-data refresh stabilization changes
- **THEN** the workflow records separate outcomes for `core` and `100` in that order
- **THEN** each stage records the command invoked, selected scope, invocation timestamp, and either typed refresh success evidence or structured blocker evidence

#### Scenario: Operator records fresh combined sync evidence
- **WHEN** an operator runs the approved `data-sync-local` smoke workflow after the staged standalone refresh review
- **THEN** the workflow records the command invoked, invocation timestamp, and the combined bootstrap-plus-refresh outcome
- **THEN** the evidence is sufficient to compare combined sync behavior with the standalone staged refresh contract without re-parsing logs

#### Scenario: Blocked staged or sync runs remain first-class evidence
- **WHEN** provider, network, runtime, or data conditions prevent a staged refresh or combined sync run from completing safely
- **THEN** the workflow records `status`, `stage`, `status_code`, and `error` plus the attempted scope and invocation timestamp
- **THEN** the runbook treats that blocked outcome as current operational evidence instead of masking it behind undocumented retries or implied success

#### Scenario: Deferred scope remains explicit in readiness posture
- **WHEN** this change completes staged smoke evidence for `core` and `100` only
- **THEN** the workflow records that `200` validation is deferred follow-up scope
- **THEN** the resulting documentation does not imply `200` readiness from `core` and `100` outcomes
