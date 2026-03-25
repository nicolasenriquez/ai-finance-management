# portfolio-accounting Specification

## Purpose
TBD - created by archiving change add-ledger-foundation-and-accounting-policy-for-dataset-1. Update Purpose after archive.
## Requirements
### Requirement: Dataset 1 accounting policy is explicit before analytics expansion
The system SHALL use an explicit, documented v1 accounting policy for dataset 1 trades, dividends, and splits before advanced analytics are implemented.

#### Scenario: Accounting policy is frozen for dataset 1 v1
- **WHEN** the portfolio-ledger foundation is introduced
- **THEN** the system defines one explicit accounting policy version for dataset 1
- **THEN** later analytics work depends on that frozen policy instead of hidden assumptions

### Requirement: Dataset 1 sells use FIFO lot matching
The system SHALL match sell-side trade quantity against prior open purchase lots using first-in-first-out order for dataset 1 v1.

#### Scenario: Sell consumes the earliest eligible lots first
- **WHEN** a sell trade is derived from persisted canonical dataset 1 records
- **THEN** the system matches the sold quantity against the oldest still-open compatible lots first
- **THEN** the resulting lot dispositions explain the realized basis used by that sell

### Requirement: Dataset 1 realized gain uses source-provided USD trade values with FIFO basis
The system SHALL interpret dataset 1 realized gain using FIFO-matched lot basis and the existing normalized USD trade values without inventing missing fee or FX adjustments.

#### Scenario: Realized gain is derived from sell proceeds and matched basis
- **WHEN** a sell trade is processed under the dataset 1 v1 accounting policy
- **THEN** realized gain is based on the sell's normalized USD proceeds and the FIFO-matched lot cost basis
- **THEN** the system does not infer additional fee or FX adjustments that are not present in the canonical source data

### Requirement: Dividends are income events and do not mutate lot basis
The system SHALL treat dataset 1 dividends as separate income events rather than as direct lot-basis mutations.

#### Scenario: Dividend is recorded independently of lot cost basis
- **WHEN** a dividend canonical record is derived into the portfolio ledger
- **THEN** the system records the gross, tax, and net dividend values as dividend-event truth
- **THEN** it does not change open-lot cost basis because of the dividend event alone

### Requirement: Splits adjust open lots proportionally without realizing gain
The system SHALL apply dataset 1 split events by adjusting affected open-lot share quantities and per-share basis proportionally while preserving total lot basis.

#### Scenario: Split updates open-lot share counts and unit basis
- **WHEN** a split event is applied to open lots for an instrument
- **THEN** the system updates share quantities according to the split ratio
- **THEN** the system adjusts unit cost basis proportionally
- **THEN** the total pre-split lot basis remains unchanged
- **THEN** no realized gain event is created solely because of the split

### Requirement: Unsupported dataset 1 accounting concerns remain explicit
The system SHALL reject hidden accounting assumptions for fee, FX, or unsupported corporate-action handling that the current dataset 1 canonical contract does not provide.

#### Scenario: Missing fee or FX fields do not produce inferred adjustments
- **WHEN** dataset 1 records lack explicit fee or FX source fields
- **THEN** the system documents those concerns as unsupported in the v1 policy
- **THEN** the accounting flow does not silently invent additional adjustments

### Requirement: Financial golden cases prove accounting behavior independently of PDF parsing
The system SHALL provide deterministic finance-focused golden cases that validate the frozen accounting policy and lot behavior separately from extraction correctness.

#### Scenario: Finance golden case proves FIFO and split behavior
- **WHEN** the portfolio-ledger tests run against the checked-in finance golden cases
- **THEN** the cases prove FIFO lot matching outcomes deterministically
- **THEN** the cases prove split-adjusted lot behavior deterministically
- **THEN** the cases remain readable enough to explain the intended accounting policy
