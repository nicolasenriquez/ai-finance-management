## MODIFIED Requirements

### Requirement: External provider adapter SHALL normalize yfinance market data into the existing ingestion contract
The system SHALL fetch supported `yfinance` quote or price-history payloads and normalize them into the existing market-data ingestion write contract before persistence, across the approved runtime close-payload shapes.

#### Scenario: Dataset_1 symbol history is fetched and normalized
- **WHEN** the system requests supported market data for a symbol already present in current `dataset_1` ledger truth
- **THEN** the adapter produces normalized market-data writes compatible with the existing ingestion service
- **THEN** the adapter preserves the canonical symbol form required to match current ledger truth

#### Scenario: Multi-symbol close payload is normalized using trading-date index keys
- **WHEN** the provider returns a tabular close payload for one or more requested symbols
- **THEN** the adapter derives market-time keys from temporal index values rather than symbol labels
- **THEN** each normalized row is attributed to the correct symbol and trading date

#### Scenario: Unsupported close payload shape is rejected
- **WHEN** a provider response close payload cannot be mapped safely into the approved shape set
- **THEN** the adapter fails explicitly before persistence
- **THEN** the system does not silently coerce or skip unmappable rows
