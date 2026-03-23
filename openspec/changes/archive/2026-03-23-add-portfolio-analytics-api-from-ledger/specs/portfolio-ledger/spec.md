## MODIFIED Requirements

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
