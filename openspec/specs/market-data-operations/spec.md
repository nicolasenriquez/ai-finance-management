# market-data-operations Specification

## Purpose
TBD - created by archiving change add-yfinance-market-data-operations. Update Purpose after archive.
## Requirements
### Requirement: Market-data operations SHALL provide a manual full-refresh workflow for the supported symbol universe
The system SHALL provide one explicit operator-facing workflow that refreshes market data for one selected supported-universe scope mode (`core`, `100`, or `200`) using the existing `yfinance` ingestion path.

#### Scenario: Operator runs a full refresh with explicit scope mode
- **WHEN** the operator triggers the market-data full-refresh workflow and selects a scope mode
- **THEN** the system requests the symbols resolved for that selected scope mode through the existing `yfinance` provider path
- **THEN** the resulting market-data writes are persisted through the existing market-data ingestion contract rather than a second write path

#### Scenario: Operator runs a full refresh without explicit scope mode
- **WHEN** the operator triggers the market-data full-refresh workflow without passing a scope mode
- **THEN** the system defaults the refresh scope mode to `core`
- **THEN** the system requests only the symbols resolved for `core`

#### Scenario: Refresh scope mode contract is validated
- **WHEN** the system receives a refresh-scope selector for operator full refresh
- **THEN** the selector is validated against the allowed typed set (`core`, `100`, `200`)
- **THEN** values outside that set are rejected explicitly before provider ingestion starts

### Requirement: Market-data operations SHALL use one explicit supported-symbol source
The system SHALL resolve full-refresh scope from one central supported-symbol contract aligned with current `dataset_1`-anchored market-data support rules, with deterministic mapping from scope mode to symbol set.

#### Scenario: Full refresh scope is resolved
- **WHEN** the system prepares a full market-data refresh for scope mode `core`, `100`, or `200`
- **THEN** it derives the requested symbols from one explicit supported-symbol source using the configured scope-to-universe mapping
- **THEN** it does not widen scope implicitly from provider responses or ad hoc operator input

### Requirement: Market-data operations SHALL fail fast on incomplete full-refresh results
The system SHALL reject a full-refresh run if any required-portfolio symbol cannot be fetched or normalized safely into the existing market-data contract, and SHALL allow bounded partial completion for `100/200` only when all unrecovered failures are outside the required-portfolio set and belong to the approved live-provider blocker categories.

#### Scenario: One required symbol in `core` refresh is unsafe
- **WHEN** one requested `core` symbol is missing, unmappable, lacks required pricing metadata, or remains blocked after approved recovery is exhausted
- **THEN** the full refresh fails explicitly
- **THEN** the system does not persist a partial full-refresh snapshot that omits the rejected required symbol

#### Scenario: Starter-scope refresh has only approved non-portfolio blocker failures
- **WHEN** a `100` or `200` refresh exhausts approved recovery for one or more requested symbols outside the required-portfolio set
- **THEN** the system may persist safe rows for the successfully fetched symbols
- **THEN** the run completes only if every failed symbol belongs to the approved blocker categories and no required-portfolio symbol failed

#### Scenario: Starter-scope refresh has an unsafe required or unsupported failure
- **WHEN** a `100` or `200` refresh includes a failed required-portfolio symbol or an unsupported provider failure outside the approved blocker categories
- **THEN** the full refresh fails explicitly
- **THEN** the system does not report that run as a successful bounded-partial completion

### Requirement: Market-data operations SHALL expose explicit refresh outcome evidence
The system SHALL produce a structured outcome for each full-refresh run that identifies the selected scope mode, requested symbol scope, retry diagnostics, failed-symbol diagnostics, and resulting snapshot provenance.

#### Scenario: Full refresh completes with strict or bounded-partial success
- **WHEN** a full-refresh run completes successfully
- **THEN** the evidence includes `refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`, `retry_attempted_symbols`, and `failed_symbols`
- **THEN** operators can distinguish strict-complete versus bounded-partial outcomes from structured evidence without re-parsing logs

#### Scenario: Full refresh fails explicitly at refresh stage
- **WHEN** a full-refresh run fails explicitly at refresh stage
- **THEN** the failure evidence includes `status`, `stage`, `status_code`, `error`, and `refresh_scope_mode`
- **THEN** the failure remains auditable as blocker evidence for the selected staged onboarding scope

### Requirement: Market-data operations SHALL expose local operator entrypoints for refresh and sync workflows
The system SHALL expose explicit local operator entrypoints for market refresh and combined data sync without requiring a new public market-data API route in this slice, and those entrypoints SHALL support optional refresh scope mode selection.

#### Scenario: Operator runs local market refresh entrypoint
- **WHEN** an operator invokes the local market-refresh command workflow with or without a scope mode
- **THEN** the system executes the existing supported-universe refresh seam through `yfinance` for the resolved scope mode
- **THEN** the workflow returns structured outcome evidence for that refresh run

#### Scenario: Operator runs local combined sync entrypoint
- **WHEN** an operator invokes the local combined sync workflow with or without a scope mode
- **THEN** the system executes bootstrap and refresh in deterministic order
- **THEN** the refresh stage uses the resolved scope mode and the workflow reports explicit success or failure status for the overall operation

#### Scenario: Operator workflows fail fast
- **WHEN** a refresh or sync stage cannot complete safely
- **THEN** the workflow exits with explicit failure and actionable context
- **THEN** the system does not treat partially completed sync stages as a successful run

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

### Requirement: Market-data operations SHALL apply conservative retry defaults and configurable request pacing
The system SHALL execute staged-scope provider refreshes with conservative default retry pressure and explicit per-symbol pacing controls, both configurable through settings, so operators can reduce throttling risk without changing code.

#### Scenario: Refresh runs with default conservative pressure controls
- **WHEN** the operator runs staged-scope refresh without overriding yfinance retry/pacing settings
- **THEN** the system uses one configured retry and default per-symbol request spacing
- **THEN** strict required-symbol fail-fast behavior remains unchanged for `core` and required symbols in `100/200`

#### Scenario: Operator adjusts retry or pacing via settings
- **WHEN** the runtime settings override retry count, retry backoff, or per-symbol request spacing
- **THEN** the refresh orchestration uses the configured values
- **THEN** the workflow preserves the same success/failure contract and evidence semantics
