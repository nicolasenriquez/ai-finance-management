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
The system SHALL produce a structured outcome for each full-refresh run that identifies the selected scope mode, requested symbol scope, retry diagnostics, recovery diagnostics, failed-symbol diagnostics, and resulting snapshot provenance.

#### Scenario: Full refresh completes with strict or recovered success
- **WHEN** a full-refresh run completes successfully
- **THEN** the evidence includes `refresh_scope_mode`, `requested_symbols`, `requested_symbols_count`, `snapshot_key`, `snapshot_captured_at`, `snapshot_id`, `inserted_prices`, `updated_prices`, `retry_attempted_symbols`, `failed_symbols`, `history_fallback_symbols`, `history_fallback_periods_by_symbol`, and `currency_assumed_symbols`
- **THEN** operators can distinguish a clean run from a run that required bounded history or currency recovery without re-parsing logs

#### Scenario: Full refresh fails explicitly after recovery exhaustion
- **WHEN** a full-refresh run fails explicitly after bounded recovery is exhausted
- **THEN** the failure evidence includes `status`, `stage`, `status_code`, `error`, and `refresh_scope_mode`
- **THEN** the failure remains auditable as blocker evidence for the selected staged onboarding scope

### Requirement: Market-data operations SHALL preserve snapshot identity for mixed-period recovery runs
The system SHALL keep snapshot identity anchored to the requested refresh contract even when one or more symbols are recovered through shorter fallback periods, and SHALL record the actual fallback periods as structured metadata and evidence instead of silently redefining snapshot identity.

#### Scenario: Mixed-period recovery still produces one requested-contract snapshot
- **WHEN** a refresh run starts with one requested primary period and one or more symbols recover through shorter fallback periods
- **THEN** the resulting `snapshot_key` remains anchored to the originally requested refresh contract
- **THEN** the actual fallback periods used per symbol are exposed in structured metadata and typed evidence

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

### Requirement: Market-data operations SHALL apply conservative retry defaults, bounded recovery caps, and configurable request pacing
The system SHALL execute staged-scope provider refreshes with conservative default retry pressure, bounded semantic recovery caps, and explicit per-symbol pacing controls, all configurable through settings, so operators can reduce throttling risk without changing code.

#### Scenario: Refresh runs with default conservative pressure controls
- **WHEN** the operator runs staged-scope refresh without overriding yfinance retry, fallback, or pacing settings
- **THEN** the system uses one configured transport retry, the configured shorter-period history ladder, and the default per-symbol request spacing
- **THEN** strict required-symbol fail-fast behavior remains unchanged for `core` and required symbols in `100/200`

#### Scenario: Operator adjusts retry, fallback, or pacing through settings
- **WHEN** the runtime settings override retry count, retry backoff, shorter-period fallback ladder, default currency, or per-symbol request spacing
- **THEN** the refresh orchestration uses the configured values while preserving bounded recovery semantics
- **THEN** the workflow preserves the same success and failure contract for required coverage and unsupported provider payloads
