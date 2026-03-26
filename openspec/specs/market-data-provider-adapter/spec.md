# market-data-provider-adapter Specification

## Purpose
TBD - created by archiving change add-yfinance-market-data-adapter. Update Purpose after archive.
## Requirements
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

### Requirement: YFinance SHALL remain the current operational provider path for market-data refresh
The system SHALL use the existing `yfinance` adapter as the approved operational provider path for the current market-data refresh slice and SHALL not require broker-authenticated provider support to perform supported-universe refreshes.

#### Scenario: Supported-universe refresh is invoked in the current phase
- **WHEN** the system performs the approved market-data refresh workflow for the current supported symbol universe
- **THEN** it executes through the existing `yfinance` adapter path
- **THEN** it does not require a broker-authenticated provider integration to complete that workflow

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
