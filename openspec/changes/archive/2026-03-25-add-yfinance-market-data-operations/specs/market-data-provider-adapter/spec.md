## ADDED Requirements

### Requirement: YFinance SHALL remain the current operational provider path for market-data refresh
The system SHALL use the existing `yfinance` adapter as the approved operational provider path for the current market-data refresh slice and SHALL not require broker-authenticated provider support to perform supported-universe refreshes.

#### Scenario: Supported-universe refresh is invoked in the current phase
- **WHEN** the system performs the approved market-data refresh workflow for the current supported symbol universe
- **THEN** it executes through the existing `yfinance` adapter path
- **THEN** it does not require a broker-authenticated provider integration to complete that workflow
