## MODIFIED Requirements

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
