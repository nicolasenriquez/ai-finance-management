# portfolio-ledger Specification

## Purpose
TBD - created by archiving change add-ledger-foundation-and-accounting-policy-for-dataset-1. Update Purpose after archive.
## Requirements
### Requirement: Portfolio ledger derives canonical finance events from persisted dataset 1 records
The system SHALL derive portfolio-domain ledger records from persisted dataset 1 canonical records in PostgreSQL without reparsing source PDFs or accepting alternate client-supplied ledger payloads.

#### Scenario: Persisted trade record becomes a portfolio transaction
- **WHEN** a persisted canonical dataset 1 trade record is processed by the portfolio-ledger derivation flow
- **THEN** the system creates one `portfolio_transaction` row for that trade
- **THEN** the derived ledger row preserves queryable lineage to the source document, import job, and canonical-record fingerprint

#### Scenario: Persisted dividend record becomes a dividend event
- **WHEN** a persisted canonical dataset 1 dividend record is processed by the portfolio-ledger derivation flow
- **THEN** the system creates one `dividend_event` row for that dividend
- **THEN** the derived ledger row preserves queryable lineage to the source document, import job, and canonical-record fingerprint

#### Scenario: Persisted split record becomes a corporate action event
- **WHEN** a persisted canonical dataset 1 split record is processed by the portfolio-ledger derivation flow
- **THEN** the system creates one `corporate_action_event` row for that split
- **THEN** the derived ledger row preserves queryable lineage to the source document, import job, and canonical-record fingerprint

### Requirement: Portfolio ledger rebuild is idempotent and duplicate-safe
The system SHALL allow the portfolio-ledger derivation flow to rerun from the same persisted canonical source input without creating duplicate ledger or lot truth.

#### Scenario: Rebuilding the same canonical input does not duplicate ledger rows
- **WHEN** the system rebuilds the portfolio ledger from canonical records whose ledger equivalents already exist
- **THEN** it does not create duplicate `portfolio_transaction`, `dividend_event`, or `corporate_action_event` rows
- **THEN** the resulting state remains attributable to deterministic uniqueness rules rather than append-only behavior

#### Scenario: Concurrent rebuild attempts remain duplicate-safe
- **WHEN** two rebuild operations process the same canonical source input concurrently
- **THEN** the database remains the final arbiter for duplicate protection
- **THEN** the resulting ledger state contains no duplicate derived rows

### Requirement: Lot and lot-disposition records are derived from ledger events instead of stored as source truth
The system SHALL derive lot state from the trade and split ledger events using the frozen accounting policy instead of treating lots as independently imported source records.

#### Scenario: Buy transaction creates an open lot
- **WHEN** a buy-side `portfolio_transaction` is derived from a persisted trade record
- **THEN** the system creates an open `lot` tied to that transaction's lineage
- **THEN** the lot stores enough basis and quantity information for later sell matching

#### Scenario: Sell transaction creates lot dispositions instead of mutating source truth
- **WHEN** a sell-side `portfolio_transaction` is processed by the lot engine
- **THEN** the system creates one or more `lot_disposition` records that explain which prior open lots were consumed
- **THEN** the original purchase lots remain auditable as the basis source of truth

#### Scenario: Split event adjusts open lots without creating artificial trades
- **WHEN** a `corporate_action_event` representing a split is processed
- **THEN** the system updates the affected open lots according to the frozen split policy
- **THEN** the system does not create a synthetic buy or sell trade to represent the split

### Requirement: Portfolio ledger writes fail transactionally
The system SHALL fail the rebuild request without partial downstream writes when canonical-to-ledger mapping or lot derivation cannot complete safely.

#### Scenario: Derivation fails during ledger rebuild
- **WHEN** the system encounters a canonical record or lot-calculation path that it cannot process under the frozen v1 rules
- **THEN** it reports an explicit failure
- **THEN** it does not commit a partial set of ledger or lot rows for that rebuild operation

### Requirement: Portfolio ledger remains separate from market data and analytics caches
The system SHALL keep transaction-ledger truth and derived lot state separate from market-data storage and presentation-oriented analytics tables, and analytics capabilities SHALL consume ledger truth in a read-only manner.

#### Scenario: Ledger foundation is added before market data
- **WHEN** this portfolio-ledger capability is implemented
- **THEN** it introduces transaction-ledger and lot-derivation tables only
- **THEN** it does not treat price history, FX rates, or analytics snapshots as part of the canonical ledger

#### Scenario: Analytics reads ledger truth without mutating it
- **WHEN** a portfolio analytics capability computes grouped or lot-level portfolio output
- **THEN** it reads from persisted ledger and lot state as the source of truth
- **THEN** it does not rewrite canonical, ledger, or lot records while producing analytics responses
