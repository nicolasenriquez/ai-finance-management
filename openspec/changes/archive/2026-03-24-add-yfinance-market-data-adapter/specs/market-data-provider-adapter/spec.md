## ADDED Requirements

### Requirement: External provider adapter SHALL normalize yfinance market data into the existing ingestion contract
The system SHALL fetch supported `yfinance` quote or price-history payloads and normalize them into the existing market-data ingestion write contract before persistence.

#### Scenario: Dataset_1 symbol history is fetched and normalized
- **WHEN** the system requests supported market data for a symbol already present in current `dataset_1` ledger truth
- **THEN** the adapter produces normalized market-data writes compatible with the existing ingestion service
- **THEN** the adapter preserves the canonical symbol form required to match current ledger truth

### Requirement: External provider adapter SHALL preserve explicit provenance and deterministic snapshot identity
The system SHALL persist provider-backed market-data writes with explicit provider provenance and a deterministic snapshot identity that remains attributable to the external fetch input.

#### Scenario: Provider-backed snapshot is ingested
- **WHEN** a `yfinance` fetch succeeds and the normalized rows are persisted
- **THEN** every resulting write includes explicit `source_type`, `source_provider`, and snapshot identity metadata
- **THEN** repeated ingests of the same provider snapshot remain attributable to deterministic snapshot-key rules

#### Scenario: Data-shaping fetch options change
- **WHEN** a provider request changes a fetch parameter that can alter the resulting dataset, such as time range, granularity, or semantic flags
- **THEN** the resulting snapshot identity changes deterministically
- **THEN** the system does not treat materially different provider fetches as the same snapshot

### Requirement: External provider adapter SHALL freeze first-slice price semantics
The system SHALL define one explicit first-slice provider price semantic for persisted `price_value` rows and SHALL not allow that meaning to vary implicitly across requests.

#### Scenario: First-slice price rows are normalized
- **WHEN** the adapter converts `yfinance` day-level data into internal market-data writes
- **THEN** `price_value` uses the documented first-slice provider price semantic
- **THEN** the semantic choice is consistent across repeated runs for the same fetch mode

### Requirement: External provider adapter SHALL fail fast on unsafe or incomplete provider payloads
The system SHALL reject provider-backed writes when required symbol, time-key, or price fields cannot be mapped safely into the existing market-data contract.

#### Scenario: Provider payload is incomplete or unmappable
- **WHEN** a `yfinance` response omits required pricing fields, required time context, or a safely mappable canonical symbol
- **THEN** the adapter fails explicitly before persistence
- **THEN** the system does not silently ingest partial or inferred rows

#### Scenario: One row in a requested provider batch is unsafe
- **WHEN** one symbol or row in the requested provider batch cannot be normalized safely
- **THEN** the whole provider-backed ingest fails before persistence
- **THEN** the system does not persist a partial snapshot that omits the rejected row

### Requirement: External provider adapter SHALL keep automated verification deterministic
The system SHALL validate provider-adapter behavior using deterministic fixtures or mocks rather than requiring live-provider access in automated tests.

#### Scenario: Automated test suite validates provider behavior
- **WHEN** unit or integration tests exercise the provider adapter
- **THEN** they use recorded or mocked provider responses
- **THEN** test outcomes do not depend on live `yfinance` network availability or upstream data volatility
