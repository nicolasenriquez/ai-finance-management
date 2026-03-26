## MODIFIED Requirements

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

## ADDED Requirements

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
