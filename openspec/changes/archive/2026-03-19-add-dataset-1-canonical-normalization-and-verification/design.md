## Context

The repository already has the first three ETL slices in place: PDF ingestion stores accepted files and returns a `storage_key`, PDF preflight determines extractability, and PDF extraction returns deterministic raw rows for dataset 1. The next backlog gap is to turn those raw rows into trusted canonical records and to verify them against the golden set before any PostgreSQL persistence or portfolio analytics work begins.

The current repo state makes this change the natural next step because the persistence layer is still empty and the extraction spec explicitly deferred normalization and verification. The implementation therefore needs a narrow contract-first slice that can consume the existing raw extraction output, preserve provenance and raw values, produce typed canonical fields deterministically, and emit a machine-readable verification report without introducing database dependencies prematurely.

## Goals / Non-Goals

**Goals:**
- Add a dedicated normalization capability for dataset 1 that maps extracted tables into canonical typed records while preserving raw values and provenance.
- Add row-level schema validation so malformed or ambiguous rows fail fast before later persistence work.
- Add deterministic verification reporting against the dataset 1 golden set with row-level and field-level mismatch evidence.
- Keep the change runnable through unit and API tests without requiring PostgreSQL.
- Preserve the repo's vertical-slice architecture and keep broker-specific parsing logic outside shared canonical schemas.

**Non-Goals:**
- PostgreSQL models, migrations, document persistence, or deduplicated transaction persistence.
- Lot derivation, accounting policy implementation, analytics formulas, or frontend work.
- OCR, secondary extraction engines, or broker-generalized parsing beyond dataset 1.
- Market data ingestion or external API integration.

## Decisions

### Add separate `pdf_normalization` and `pdf_verification` feature slices
Normalization and verification are distinct product capabilities with different contracts and failure modes. Keeping them in dedicated slices preserves vertical ownership and avoids folding canonical parsing into `app/pdf_extraction/` or mixing reconciliation logic into future persistence code.

Alternative considered:
- Extend `app/pdf_extraction/` to normalize values directly: rejected because the extraction spec intentionally keeps raw extraction separate from mapping and parsing, and changing that boundary would make failures harder to isolate.

### Use `storage_key` as the input boundary for normalization and verification
The existing ETL spine already uses a stored-upload handoff, so the next slices should accept `storage_key`, resolve the stored PDF through existing boundaries, and reuse extraction internally. This keeps the workflow coherent and avoids forcing clients to pass large intermediate payloads or duplicate uploads.

Alternative considered:
- Accept raw extraction payloads directly at the API boundary: rejected because it duplicates internal contracts and creates a second public source of truth before the canonical schema is stable.

### Introduce canonical record types that stay broker-agnostic but dataset-1 scoped
The change should emit typed canonical records for the three dataset 1 table groups while preserving raw source fields separately. The canonical contract should represent stable finance concepts such as trade activity, dividend activity, and split events rather than broker-column names, but it should avoid overreaching into later ledger, lot, or pricing models.

Alternative considered:
- Reuse broker-specific field names in the canonical schema: rejected because ADR-012 explicitly requires broker logic to stay outside canonical contracts.

### Make schema validation part of normalization, not a later persistence concern
The normalizer should enforce row-level invariants immediately after mapping so bad data fails fast and verification reports remain trustworthy. This includes explicit handling for blank-to-null conversion, typed date and decimal parsing, and deterministic trade-direction derivation only when the source data makes it unambiguous.

Alternative considered:
- Delay validation until persistence time: rejected because that would allow invalid canonical output to propagate into later slices and make mismatch diagnosis harder.

### Emit a deterministic verification report against the checked-in golden set
Verification should compare normalized output to the dataset 1 golden set and return a stable machine-readable report containing counts, pass/fail summary, and field-level mismatch evidence with provenance. The report should remain explainable and diff-friendly so regressions can be diagnosed quickly.

Alternative considered:
- Limit verification to ad hoc test assertions only: rejected because the PRD and backlog require a reusable verification artifact, not just implicit test coverage.

### Keep persistence and fingerprints explicitly out of this change
This change should stop at trusted canonical records and verification evidence. Persistence, document-level idempotency, and transaction fingerprints depend on the canonical contract produced here, so designing those before the contract is frozen would increase rework risk.

Alternative considered:
- Bundle persistence into the same change: rejected because the database layer is currently empty and would force schema, deduplication, and migration decisions before the canonical output contract is proven.

## Risks / Trade-offs

- [Canonical field mapping may overfit dataset 1 and become awkward for future sources] -> Keep the first contract broker-agnostic in naming but intentionally scoped to current table types and provenance needs only.
- [Locale-specific parsing can introduce subtle numeric or date bugs] -> Lock parsing rules with focused unit tests for decimal commas, currency strings, blank cells, and invalid combinations before implementation broadens.
- [Adding new API contracts too early can harden unstable shapes] -> Keep response models minimal, typed, and explicitly scoped to dataset 1 normalization and verification rather than promising broader ledger semantics.
- [Verification may fail noisily if the golden set and canonical contract drift] -> Make mismatch evidence explicit and update affected docs whenever the contract changes.
- [This slice increases dependency on extraction stability] -> Reuse extraction as-is and keep normalization tests narrow so failures can be attributed to the correct stage.

## Migration Plan

1. Confirm the dataset 1 canonical expectations and verification evidence requirements from the checked-in golden set and reference guides.
2. Add dedicated `app/pdf_normalization/` and `app/pdf_verification/` slices with typed schemas, services, routes, and tests.
3. Reuse the existing extraction service as the upstream input boundary via `storage_key`.
4. Add deterministic normalization, row validation, and verification-report generation backed by dataset 1 tests.
5. Update affected docs and `CHANGELOG.md` so repo history clearly marks canonical normalization and verification as complete while persistence remains pending.

## Open Questions

None for current scope.
