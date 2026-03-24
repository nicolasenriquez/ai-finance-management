## ADDED Requirements

### Requirement: Market data SHALL persist separately from canonical transactions and ledger truth
The system SHALL store market data in dedicated persistence structures that remain separate from canonical PDF records, portfolio ledger events, lots, lot dispositions, and derived analytics tables.

#### Scenario: Market data schema is introduced
- **WHEN** market-data ingestion is implemented
- **THEN** quote and price-history records are stored outside canonical and ledger tables
- **THEN** the schema does not treat market data as part of transaction-ledger truth

### Requirement: Market data refresh SHALL preserve explicit provenance
The system SHALL preserve source provenance for every persisted market-data record so downstream analytics can identify which provider and snapshot produced a given value.

#### Scenario: Persisted quote includes provenance
- **WHEN** a quote or historical price is written to storage
- **THEN** the persisted record includes the source/provider identifier
- **THEN** the persisted record includes the market timestamp or trading-date context used for that value
- **THEN** the persisted record includes ingestion-time or snapshot-batch provenance sufficient for auditing

### Requirement: Initial market-data symbol support SHALL match current dataset_1 ledger truth
The first market-data ingestion slice SHALL support the instrument symbols already present in persisted `dataset_1` ledger truth and SHALL preserve their canonical symbol forms instead of inferring simplified substitutes.

#### Scenario: Current dataset_1 symbol shapes are ingested safely
- **WHEN** the system persists market data for an instrument already present in current ledger truth, including dotted symbols such as `BRK.B`
- **THEN** it stores the symbol in its canonical form required to match persisted ledger truth
- **THEN** it does not silently rewrite that symbol into a lossy substitute during persistence

### Requirement: Market data refresh SHALL be idempotent for the same source snapshot
The system SHALL prevent ambiguous duplicate market-data rows when the same provider snapshot or price point is ingested more than once.

#### Scenario: Same source snapshot is refreshed twice
- **WHEN** the system ingests a market-data payload that matches an already persisted provider/source and time key
- **THEN** it does not create a second logically duplicate market-data row
- **THEN** the resulting stored state remains attributable to deterministic uniqueness rules

### Requirement: Market data refresh SHALL not mutate canonical or ledger truth
The system SHALL treat market-data ingestion as a separate write path that does not create, update, or delete canonical transaction, portfolio-ledger, lot, or lot-disposition truth.

#### Scenario: Quote refresh runs after ledger truth exists
- **WHEN** a market-data refresh succeeds or fails
- **THEN** canonical PDF records remain unchanged
- **THEN** portfolio transactions, dividend events, corporate action events, lots, and lot dispositions remain unchanged

### Requirement: Market data failures SHALL remain explicit and fail-fast
The system SHALL reject market-data writes that lack required provenance or key pricing fields instead of silently degrading to partial or inferred persistence behavior.

#### Scenario: Required market-data fields are missing
- **WHEN** a market-data payload cannot provide the required provider/source identity or the required symbol and time key for persistence
- **THEN** the write is rejected with an explicit failure
- **THEN** the system does not persist a partial market-data row with inferred defaults

#### Scenario: Unsupported symbol shape cannot be mapped safely
- **WHEN** a market-data payload cannot be mapped to the canonical symbol form required for persisted ledger truth
- **THEN** the write is rejected with an explicit failure
- **THEN** the system does not persist a market-data row under an inferred fallback symbol
