## MODIFIED Requirements

### Requirement: Portfolio summary API exposes only ledger-supported KPI fields in v1
The system SHALL continue to expose the current ledger-supported KPI fields in grouped portfolio summary responses and, when a consistent persisted market-data snapshot is available for the open-position symbols in the response, SHALL additionally expose bounded market-enriched valuation fields without inventing FX-dependent or unsupported values.

#### Scenario: Summary row includes ledger and market-enriched KPI fields
- **WHEN** a grouped portfolio summary row is returned for an instrument with an open position and safe pricing coverage in the selected snapshot
- **THEN** it includes the existing ledger-backed fields (`open_quantity`, `open_cost_basis_usd`, `open_lot_count`, `realized_proceeds_usd`, `realized_cost_basis_usd`, `realized_gain_usd`, `dividend_gross_usd`, `dividend_taxes_usd`, `dividend_net_usd`)
- **THEN** it additionally includes the bounded market-enriched valuation fields defined for this slice
- **THEN** it does not invent FX-sensitive or unsupported values beyond the documented pricing contract

#### Scenario: Closed-position row does not require valuation fields
- **WHEN** a grouped portfolio summary row is returned for an instrument with no remaining open quantity
- **THEN** the row still includes the existing ledger-backed fields
- **THEN** valuation fields may remain unset or null for that row because no open position requires current pricing

## ADDED Requirements

### Requirement: Portfolio summary API exposes explicit pricing provenance for market-enriched KPIs
The system SHALL include explicit market-data provenance in grouped portfolio summary responses whenever market-enriched valuation fields are present, so clients can identify which persisted market-data snapshot produced the valuation results.

#### Scenario: Summary response includes pricing provenance
- **WHEN** the system returns a grouped portfolio summary response with market-enriched valuation fields
- **THEN** the payload includes explicit pricing provenance such as the selected snapshot identity and pricing timestamp context
- **THEN** clients can distinguish ledger-state freshness from market-data freshness

### Requirement: Portfolio summary API uses one consistent persisted market-data snapshot per response
The system SHALL compute market-enriched grouped summary KPIs from one explicit persisted market-data snapshot rather than mixing independently selected latest rows across symbols.

#### Scenario: Summary valuation uses one selected snapshot
- **WHEN** the system computes a grouped portfolio summary with market-enriched KPI fields
- **THEN** all price-backed valuation fields in that response are derived from the same selected persisted market-data snapshot
- **THEN** the response does not mix valuation rows from different snapshot identities

### Requirement: Portfolio summary API fails explicitly when required open-position price coverage is incomplete
The system SHALL reject market-enriched grouped summary responses when an instrument with open quantity in the portfolio does not have safe pricing coverage in the selected persisted market-data snapshot.

#### Scenario: Required open-position symbol is missing from selected snapshot
- **WHEN** the system cannot find safe persisted price coverage in the selected snapshot for an instrument whose grouped summary row has open quantity greater than zero
- **THEN** the grouped summary request fails explicitly
- **THEN** the system does not silently omit valuation fields, mix fallback rows from another snapshot, or report a partial portfolio valuation as complete
