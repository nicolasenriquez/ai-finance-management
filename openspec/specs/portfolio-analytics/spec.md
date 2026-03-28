# portfolio-analytics Specification

## Purpose
TBD - created by archiving change add-portfolio-analytics-api-from-ledger. Update Purpose after archive.
## Requirements
### Requirement: Portfolio summary API groups analytics by instrument from ledger truth
The system SHALL provide a portfolio summary API that groups analytics by `instrument_symbol` using persisted portfolio-ledger and lot state rather than reparsing PDFs or accepting client-supplied portfolio totals.

#### Scenario: Grouped summary returns one row per instrument with open position or realized activity
- **WHEN** the analytics service reads the current portfolio state
- **THEN** it returns one summary row per `instrument_symbol` present in persisted ledger truth
- **THEN** each row is derived from `lot`, `lot_disposition`, `portfolio_transaction`, and `dividend_event` data as applicable

### Requirement: Portfolio analytics responses expose explicit ledger-state consistency metadata
The system SHALL include an explicit `as_of_ledger_at` timestamp in both grouped summary and lot-detail responses to indicate the persisted ledger state used for analytics computation.

#### Scenario: Summary and lot detail include ledger as-of timestamp
- **WHEN** the system returns a grouped summary response or lot-detail response
- **THEN** the payload includes `as_of_ledger_at`
- **THEN** clients can determine the exact persisted ledger state time used for computation

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

### Requirement: Lot detail API explains per-instrument lot state from ledger truth
The system SHALL provide a lot detail API for one `instrument_symbol` that returns explainable lot rows derived from ledger truth and linked disposition history.

#### Scenario: Lot detail returns explainable lots for one instrument
- **WHEN** a client requests lot detail for an existing `instrument_symbol`
- **THEN** the system returns the lots opened for that instrument with their remaining quantity and basis fields
- **THEN** the response includes enough linked disposition detail to explain how sell-side activity consumed prior lots

### Requirement: Lot detail symbol matching is normalized and deterministic
The system SHALL normalize lot-detail symbol inputs by trimming whitespace and matching case-insensitively, while preserving one canonical uppercase symbol representation in the response.

#### Scenario: Lot detail resolves case and whitespace variants
- **WHEN** a client requests lot detail with a symbol variant such as mixed case or surrounding whitespace
- **THEN** the system resolves it against persisted ledger truth using normalized symbol matching
- **THEN** the response uses the canonical uppercase symbol representation

### Requirement: Analytics APIs remain read-only over the ledger
The system SHALL keep analytics API behavior read-only and must not mutate canonical, ledger, lot, or market-data state while serving summary or lot-detail responses.

#### Scenario: Portfolio analytics request does not change ledger truth
- **WHEN** a client requests grouped summary or lot detail
- **THEN** the system reads persisted ledger and lot data only
- **THEN** it does not create, update, or delete canonical, ledger, lot, or market-data rows as part of the request

### Requirement: Analytics APIs do not trigger rebuild side effects
The system SHALL not trigger portfolio-ledger rebuild operations during analytics request handling and SHALL only consume already-persisted derived ledger state.

#### Scenario: Analytics request does not invoke rebuild
- **WHEN** a client requests grouped summary or lot detail
- **THEN** the system does not call ledger rebuild operations
- **THEN** stale or missing derived ledger state remains an explicit upstream issue instead of an implicit analytics-side mutation

### Requirement: Analytics APIs fail explicitly for unsupported symbol requests
The system SHALL reject unsupported or unknown lot-detail requests with explicit client-facing failure instead of ambiguous empty success when the requested instrument cannot be resolved safely, and frontend consumers SHALL map this response to a dedicated not-found UI state.

#### Scenario: Lot detail rejects unknown instrument symbol
- **WHEN** a client requests lot detail for an `instrument_symbol` that has no matching persisted ledger truth
- **THEN** the system returns an explicit client error
- **THEN** the response makes clear that the requested instrument was not found in the portfolio ledger
- **THEN** frontend consumers display a not-found state rather than an empty success table

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
