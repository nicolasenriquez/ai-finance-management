## Context

The repository already has the full dataset 1 PDF ETL spine in place: ingestion, preflight, extraction, normalization, verification, and PostgreSQL persistence. The newest archived change explicitly stopped at `canonical_pdf_record` as an audit-grade persistence layer and deferred final ledger modeling, lot derivation, accounting policy, market data, and analytics until the next phase.

The roadmap and accepted ADRs make the sequencing explicit: a ledger-first model and frozen accounting policy must exist before portfolio analytics APIs are treated as trustworthy. The current codebase also has no portfolio or analytics slice registered in the application, which means the next natural implementation boundary is not endpoints or UI work but the domain foundation those later slices will depend on.

The dataset 1 canonical model currently emits only three event families:

- `trade`
- `dividend`
- `split`

That constraint matters. This change should freeze only the accounting and ledger behavior supported by those existing events and source fields, while documenting deferred cases such as independent fee events, FX conversions, market data valuation, and multi-source reconciliation.

## Goals / Non-Goals

**Goals:**
- Introduce the minimum ledger-domain entities needed to turn persisted canonical dataset 1 records into stable portfolio truth for later analytics.
- Keep `canonical_pdf_record` immutable as ETL audit truth and derive ledger records from it with explicit lineage.
- Freeze a v1 accounting policy for dataset 1 that is concrete enough to support deterministic lot derivation and future realized/unrealized gain logic.
- Add deterministic financial golden cases that prove ledger derivation and accounting behavior independently of extraction correctness.
- Keep the ledger rebuild idempotent and duplicate-safe when rerun from the same persisted canonical input.

**Non-Goals:**
- Analytics endpoints, KPI formulas, grouped portfolio APIs, or frontend work.
- Market data tables, quote refresh, price history, or FX-rate ingestion.
- Multi-broker or multi-account modeling beyond the current single-source dataset 1 workflow.
- Broadening canonical normalization to new event types that are not already emitted by dataset 1.

## Decisions

### Keep `canonical_pdf_record` as immutable ETL audit truth and derive ledger rows separately
The current persistence layer already preserves raw values, typed canonical payloads, provenance, and duplicate-safe rerun behavior. That table should remain the ETL audit boundary. The portfolio ledger should be a downstream derivation layer, not a replacement for canonical ETL storage.

This preserves one clean chain:

`source_document` -> `import_job` -> `canonical_pdf_record` -> `portfolio_transaction` / `dividend_event` / `corporate_action_event` -> `lot` / `lot_disposition`

Alternative considered:
- Treat `canonical_pdf_record` as the final analytics ledger: rejected because it keeps finance policy implicit, mixes ETL payload storage with domain truth, and would make later analytics logic harder to explain.

### Introduce only the minimum portfolio-domain entities needed before analytics
The change should add the smallest domain model that supports lot derivation from the currently supported event families:

- `portfolio_transaction` for trade events
- `dividend_event` for dividend cash income
- `corporate_action_event` for split events
- `lot` for open purchase lots
- `lot_disposition` for sell-to-lot matching outcomes

This is intentionally smaller than the guide's broader long-term domain model. It avoids premature introduction of `price_history`, `position_snapshot`, `fx_rate`, or broad account/instrument abstractions that the current dataset does not require yet.

Alternative considered:
- Add the full long-term model now (`broker_account`, `instrument`, `price_history`, `position_snapshot`, etc.): rejected because it would broaden scope beyond the current phase and increase schema churn before analytics and market-data contracts are ready.

### Derive ledger state from persisted canonical input, not directly from source PDFs
Ledger derivation should consume persisted canonical records that already passed normalization and persistence constraints. This keeps finance logic downstream of the trusted ETL boundary and avoids duplicate parsing or canonical-shape drift.

Alternative considered:
- Derive lots directly from normalization output or raw PDFs: rejected because it bypasses the new persistence boundary and weakens replay and audit clarity.

### Freeze the first accounting policy explicitly as FIFO for dataset 1 trades
The v1 accounting policy should be concrete and versioned in code and documentation. For dataset 1:

- buy trades create lots using `aporte_usd` as total cost basis
- sell trades consume prior open lots using FIFO matching
- realized gain is based on FIFO-matched lot cost basis versus sell proceeds from `rescate_usd`
- unrealized gain is policy-defined but not yet computed until market data exists
- dividends are income events and do not mutate lot cost basis
- splits adjust open-lot share counts and per-share basis proportionally without realizing gain
- fee and FX adjustments are not inferred because dataset 1 does not emit separate fee or FX fields

Alternative considered:
- Defer the accounting policy to the analytics phase: rejected because the roadmap and ADRs explicitly say analytics should not depend on hidden assumptions.

### Keep unsupported accounting cases explicit instead of inventing hidden behavior
The dataset 1 source does not currently provide independent fee events, explicit FX rates, or broader corporate-action families beyond splits. This change should document those gaps and make them explicit non-goals of the v1 accounting policy rather than filling them with assumptions.

Alternative considered:
- Infer fees or FX handling from available USD fields: rejected because the repo's fail-fast and no-inference principles make that too risky.

### Make ledger rebuild idempotent and database-arbitrated
Like the PDF persistence layer, ledger derivation should be safe to rerun from the same canonical source input. Database uniqueness constraints should remain the final arbiter for duplicate races, and reruns should reconcile to reuse-or-skip outcomes rather than duplicate ledger truth.

Alternative considered:
- Rely on app-side prechecks only: rejected because reruns and concurrent rebuilds could still create duplicate ledger state.

### Keep this change internal to domain services and persistence boundaries
This phase should not add public analytics endpoints yet. The goal is to build a trustworthy domain foundation, not present unfinished metrics. Validation can happen through service-level tests, database integration tests, and finance golden cases.

Alternative considered:
- Expose portfolio endpoints immediately after adding ledger tables: rejected because it would mix Phase 3 and Phase 4 concerns and encourage KPI work before the policy is locked.

### Add deterministic financial golden cases as a first-class contract
Extraction golden sets already prove ETL correctness. This phase should add finance-focused golden cases that prove:

- FIFO lot allocation
- realized gain matching
- split-adjusted open lots
- dividend handling as separate income events
- idempotent ledger rebuild from the same canonical source set

These cases should live close to the ledger slice and remain independent of PDF parsing.

Alternative considered:
- Rely only on ad hoc unit tests: rejected because later analytics claims need a durable, explainable finance contract.

## Risks / Trade-offs

- [The minimal ledger model may still need refactoring when market data or multi-source ingestion arrives] -> Keep this change intentionally limited to dataset 1 trade, dividend, and split behavior and document deferred entities explicitly.
- [FIFO may not be the long-term preferred accounting method for every future source] -> Version the accounting policy and scope it to dataset 1 v1 so later policy changes remain explicit migrations rather than silent behavior drift.
- [Derived lot state can become difficult to trust if canonical-to-ledger mapping is implicit] -> Preserve lineage from every derived row back to canonical source identifiers and fingerprints.
- [Keeping this phase internal may feel less product-visible than building endpoints] -> Accept that trade-off because it reduces rework and keeps analytics from hardening on top of unstable accounting assumptions.
- [The current canonical schema may not contain every future finance attribute needed downstream] -> Use this phase to lock only the behavior supported by the existing canonical records and treat missing fields as explicit blockers for later expansion.

## Migration Plan

1. Freeze the proposal, ledger spec, and accounting spec so the phase boundary is explicit before implementation.
2. Add failing finance tests and golden cases that lock the desired ledger and accounting behavior.
3. Add portfolio-ledger models and Alembic migrations for the minimal ledger and lot tables.
4. Implement canonical-to-ledger derivation and FIFO lot allocation from persisted canonical records.
5. Prove idempotent reruns and split/dividend handling through targeted and integration validation.
6. Update product and guide documents plus `CHANGELOG.md` so the repository records the frozen policy and new ledger boundary.

Rollback strategy:
- Drop the new ledger tables and keep `canonical_pdf_record` as the unchanged upstream source of truth.
- Because this phase derives downstream rows from persisted canonical input, rollback should not require rewriting the ETL or persistence layers.

## Open Questions

- None. This proposal intentionally freezes the v1 policy and keeps deferred concerns explicit so `/plan` can proceed without new design blockers.
