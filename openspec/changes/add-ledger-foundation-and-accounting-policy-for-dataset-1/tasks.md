## 0. Investigation

- [ ] 0.1 Confirm the exact Phase 3 boundary from the roadmap, ADRs, ledger guide, and current persistence design before coding
Notes: Keep this change inside ledger foundation plus accounting-policy freeze. Do not expand into analytics endpoints, market data, or frontend work.
- [ ] 0.2 Confirm which dataset 1 event types and fields are actually available from `canonical_pdf_record` before freezing accounting rules
Notes: Ground the policy in existing `trade`, `dividend`, and `split` records only, and document unsupported fee or FX handling explicitly.
- [ ] 0.3 Diagnose blast radius across migrations, persistence coupling, lot derivation, validation assets, and later analytics dependencies
Notes: Explicitly decide whether `canonical_pdf_record` remains immutable upstream audit truth and whether ledger rebuild stays internal to services in this phase.

## 1. Contract and failing tests

- [ ] 1.1 Add failing unit tests for canonical-to-ledger event mapping and lineage preservation
Notes: Cover trades, dividends, and splits deriving from persisted canonical records without reparsing source PDFs.
- [ ] 1.2 Add failing unit tests for FIFO lot matching, realized-basis accounting, and split-adjusted open lots using deterministic finance cases
Notes: Finance tests should be independent of PDF parsing and easy to audit by reading the fixtures.
- [ ] 1.3 Add failing integration tests for duplicate-safe ledger rebuilds from existing persisted canonical input
Notes: Rebuilding from the same source data must not create duplicate ledger, lot, or lot-disposition truth.

## 2. Ledger schema and policy foundation

- [ ] 2.1 Define typed ledger and accounting-policy schemas/constants for dataset 1 v1
Notes: Freeze one explicit policy version and keep unsupported fee/FX behavior explicit rather than implied.
- [ ] 2.2 Add SQLAlchemy models and Alembic migration(s) for the minimal ledger and lot tables
Notes: Keep market-data and analytics-cache entities out of scope in this phase.
- [ ] 2.3 Add checked-in finance golden cases that lock FIFO, dividend, and split behavior for dataset 1
Notes: Golden cases are part of the contract, not optional test convenience.

## 3. Ledger derivation implementation

- [ ] 3.1 Create a dedicated portfolio-ledger service that derives ledger events from persisted canonical records transactionally
Notes: Reuse persisted canonical input and preserve lineage back to source documents, import jobs, and canonical fingerprints.
- [ ] 3.2 Implement FIFO lot derivation and lot-disposition logic for buy, sell, and split flows
Notes: Dividends remain separate income events and must not mutate lot basis.
- [ ] 3.3 Enforce idempotent and duplicate-safe ledger rebuild behavior for reruns and concurrent rebuilds
Notes: Database uniqueness remains the final arbiter for duplicate races in this slice.

## 4. Validation and documentation

- [ ] 4.1 Run targeted and integration validation for the ledger foundation slice
Notes: Expected checks include targeted `pytest`, integration/database validation, `ruff`, `black --check --diff`, `bandit`, `mypy`, `pyright`, and `ty`.
- [ ] 4.2 Update affected product and guide documents to record the frozen accounting policy and ledger boundary
Notes: Reflect the new contract in roadmap-adjacent guidance without claiming analytics or market-data support yet.
- [ ] 4.3 Update `CHANGELOG.md` and any affected OpenSpec or validation references after implementation
Notes: Record the ledger foundation as the prerequisite phase before analytics APIs and frontend work.
