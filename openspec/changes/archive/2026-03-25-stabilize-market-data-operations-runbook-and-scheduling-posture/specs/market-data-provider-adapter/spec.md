## ADDED Requirements

### Requirement: External provider adapter SHALL accept approved live day-level date-key variants for operational refresh
The system SHALL normalize the approved live `yfinance` day-level response variants needed by the current operational refresh workflow without weakening fail-fast rejection for unsupported payload semantics.

#### Scenario: Live refresh payload uses an approved date-key variant
- **WHEN** the provider returns a supported day-level payload shape whose temporal key is represented by an approved live date-key variant
- **THEN** the adapter derives the correct trading-date value for each normalized row
- **THEN** the operational refresh workflow continues through the existing ingestion contract without requiring manual payload rewriting

#### Scenario: Live refresh payload uses an unsupported temporal variant
- **WHEN** the provider returns a day-level payload whose temporal key cannot be mapped safely into the approved shape set
- **THEN** the adapter fails explicitly before persistence
- **THEN** the system records the rejection as blocker evidence rather than silently coercing or skipping the unsafe payload
