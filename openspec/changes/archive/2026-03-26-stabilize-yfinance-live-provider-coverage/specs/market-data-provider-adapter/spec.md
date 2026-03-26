## MODIFIED Requirements

### Requirement: External provider adapter SHALL classify approved live-provider blocker patterns before final rejection
The system SHALL treat the approved live `yfinance` blocker patterns (`empty history` for the requested period and missing currency metadata after approved metadata reads) as bounded symbol-scoped recovery candidates before classifying a requested symbol as failed. Recovery SHALL be limited to a configured ordered shorter-period history ladder and one explicit configured default-currency assignment for missing metadata only.

#### Scenario: Empty history recovers through a shorter configured period
- **WHEN** a requested symbol returns empty history for the primary configured period
- **THEN** the adapter retries that symbol against the configured ordered shorter-period ladder until one non-empty history result is found or the ladder is exhausted
- **THEN** the adapter records which shorter period produced the accepted rows

#### Scenario: Empty history remains unresolved after the configured ladder
- **WHEN** a requested symbol still returns empty history after the configured shorter-period ladder is exhausted
- **THEN** the adapter surfaces an explicit symbol-scoped failure reason for exhausted history coverage
- **THEN** the system does not invent price rows or pretend the symbol has provider coverage

#### Scenario: Missing currency metadata uses the configured operational default
- **WHEN** a requested symbol yields valid day-level price rows but the approved metadata reads still omit currency
- **THEN** the adapter assigns the configured operational default currency code for that symbol
- **THEN** the adapter records that the symbol used assumed default currency rather than provider-supplied currency

#### Scenario: Explicit unsupported currency metadata still fails fast
- **WHEN** the provider returns an explicit currency value that cannot be normalized into the approved currency-code contract
- **THEN** the adapter fails explicitly for that symbol
- **THEN** the system does not replace the unsupported provider value with the default currency
