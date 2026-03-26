## ADDED Requirements

### Requirement: External provider adapter SHALL classify approved live-provider blocker patterns before final rejection
The system SHALL treat the currently approved live `yfinance` blocker patterns (`empty history` and missing currency metadata) as explicit symbol-scoped recovery candidates before classifying a requested symbol as failed for the operational refresh workflow.

#### Scenario: Approved currency-metadata recovery succeeds
- **WHEN** a requested symbol lacks currency metadata on the first approved provider access path
- **THEN** the adapter attempts the bounded fallback path defined for the current operational contract
- **THEN** the symbol continues through normalization only if the fallback yields one valid currency code without inference

#### Scenario: Approved blocker recovery is exhausted
- **WHEN** a requested symbol still returns empty history or lacks currency metadata after the approved recovery path is exhausted
- **THEN** the adapter surfaces an explicit symbol-scoped failure reason for that blocker category
- **THEN** the system does not silently invent price rows, currency values, or symbol coverage
