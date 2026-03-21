## Context

The repository already has the ETL spine needed to ingest a PDF, preflight it, extract deterministic raw rows, normalize those rows into canonical records, and verify them against the dataset 1 golden contract. The next backlog gap is persistence: the MVP still lacks PostgreSQL-backed storage for source-document metadata and canonical records, and the current Alembic baseline is still empty.

This change should introduce persistence without prematurely freezing the later ledger and analytics model. The persistence layer therefore needs to preserve audit truth, provenance, and duplicate-safe behavior now, while keeping lot derivation, accounting rules, and market-data concerns out of scope until the roadmap reaches those phases.

## Goals / Non-Goals

**Goals:**
- Add a dedicated `pdf_persistence` capability that persists dataset 1 document metadata and canonical records in PostgreSQL.
- Preserve audit-ready provenance, raw values, and deterministic canonical payloads for every persisted record.
- Enforce document-level idempotency using the existing uploaded file SHA-256 hash.
- Enforce duplicate-safe record persistence using deterministic, versioned fingerprints built from stable canonical business fields and explicit source identity.
- Keep persistence transactional so failed normalization or database writes do not leave partial state behind.
- Add migrations and integration tests that prove first-write, rerun, and duplicate-safe behaviors locally.

**Non-Goals:**
- Final ledger modeling for lots, positions, realized gains, or accounting policy.
- Market data tables, quote refresh, or external broker API ingestion.
- Frontend, analytics endpoints, or KPI calculation logic.
- Cross-broker generalization beyond the current dataset 1 PDF pipeline.

## Decisions

### Add a dedicated `pdf_persistence` feature slice
Persistence has a distinct contract and failure mode from ingestion, normalization, and verification. A dedicated slice keeps vertical ownership clear and avoids pushing database concerns back into upstream ETL slices that are already working and documented.

Alternative considered:
- Extend `pdf_ingestion` or `pdf_normalization` to write directly to PostgreSQL: rejected because it would blur existing capability boundaries and make persistence failures harder to isolate from ETL failures.

### Use `storage_key` as the persistence entry boundary and reuse normalization internally
The persistence flow should accept a stored upload reference, load the durable ingestion metadata manifest for source-document fields, then reuse trusted normalization output inside the service. This keeps the public boundary aligned with the existing ETL workflow and prevents clients from submitting alternate intermediate payloads that bypass the canonical pipeline.

Alternative considered:
- Accept client-submitted canonical JSON for persistence: rejected because it would create a second source of truth and weaken the contract-first ETL boundary.

### Persist three persistence-domain entities: `source_document`, `import_job`, and `canonical_pdf_record`
This change should store one deduplicated source-document row per unique uploaded PDF, one import-job row per successful committed persistence run, and one canonical-record row per unique persisted dataset 1 record. Using a generic canonical record table preserves the current normalized contract and provenance without prematurely splitting into final ledger entities before the accounting and ledger phases are defined.

Alternative considered:
- Introduce final ledger tables now (`portfolio_transaction`, `dividend_event`, `corporate_action`): rejected because Phase 3 still needs to freeze accounting-policy and ledger boundaries, and forcing those decisions now would increase schema churn risk.

### Use deterministic unique keys for both document and canonical-record persistence
The uploaded PDF SHA-256 should be the document idempotency key. Canonical records should use a deterministic fingerprint built from stable normalized business fields plus stable provenance fallback that does not depend on database-generated IDs. For dataset 1, the first fingerprint version should include:

- common fields for every record: `source_type`, `source_system`, `event_type`, `fingerprint_version`
- trades: `trade_date`, `instrument_symbol`, `trade_side`, `aporte_usd`, `rescate_usd`, `acciones_compradas_qty`, `acciones_vendidas_qty`, `table_name`, `row_index`, `source_page`
- dividends: `dividend_date`, `instrument_symbol`, `gross_usd`, `taxes_usd`, `net_usd`, `table_name`, `row_index`, `source_page`
- splits: `split_date`, `instrument_symbol`, `shares_before_qty`, `shares_after_qty`, `split_ratio_value`, `table_name`, `row_index`, `source_page`

For this change, use `source_type = "pdf_statement"`, `source_system = "broker_pdf_dataset_1"`, and `fingerprint_version = "v1"`. Persistence should insert missing rows and skip duplicates rather than erroring on valid reruns.

Alternative considered:
- Deduplicate using row provenance only (`row_id`, `row_index`, `source_page`): rejected because those fields are useful audit metadata but not the stable business identity required by the PRD for duplicate-safe persistence.

### Version persisted canonical records explicitly
Persistence should store both `fingerprint_version` and `canonical_schema_version` with every canonical record. This keeps reruns auditable when normalization evolves and avoids forcing hidden assumptions about how older persisted rows were derived.

For this change, use `canonical_schema_version = "dataset_1_v1"`.

Alternative considered:
- Rely on implicit code version or migration history: rejected because replay and duplicate diagnosis would become ambiguous as soon as normalization rules change.

### Treat verification as a validation gate, not a runtime prerequisite for writes
The persistence flow should depend on trusted normalization output but should not require a passing verification report at runtime. Verification remains a dataset-1 quality gate for tests, validation workflows, and operator confidence; persistence is the product capability that writes trusted canonical output once normalization succeeds.

Alternative considered:
- Require verification to pass before every persistence write: rejected because verification is tied to the current golden-set workflow and would couple runtime persistence behavior too tightly to dataset-specific validation.

### Keep first-seen source-document metadata canonical
When the same PDF bytes are uploaded more than once, the existing `source_document` row should remain canonical and retain the first-seen filename, storage key, and related metadata. Later successful persistence runs should create new import jobs linked to that source document rather than mutating the deduplicated document row.

Alternative considered:
- Overwrite source-document metadata on duplicate upload: rejected because it would make document identity and audit history less stable.

### Persist raw values, normalized payload, and provenance together
Each stored canonical record should preserve the original raw values, normalized typed content, and provenance needed for audit and reprocessing. Keeping these together allows later ledger phases to derive trusted records without reparsing the original PDF or losing evidence needed to explain a stored row.

Alternative considered:
- Persist only selected typed columns and drop raw payloads: rejected because it would reduce explainability and make later debugging or replay workflows harder.

### Let the database arbitrate duplicate races
The service should treat database uniqueness constraints as the source of truth for concurrent duplicate requests. `source_document.sha256` and `canonical_pdf_record.fingerprint` should be protected by unique constraints, and the persistence service should interpret uniqueness conflicts as reuse or duplicate-skip outcomes rather than business errors.

Alternative considered:
- Perform app-side existence checks only before insert: rejected because concurrent persistence requests could still create duplicate rows or produce flaky behavior under race conditions.

### Keep persistence all-or-nothing for a single request
Each persistence request should run in one database transaction: resolve or create the source document, create an import job, persist missing canonical records, and commit only if the full operation succeeds. Failed requests should be captured through structured logs rather than committed database audit rows in this slice. This protects the fail-fast policy and avoids partial imports that would be hard to reason about later.

Alternative considered:
- Commit document and record inserts in separate steps: rejected because partial success would complicate rerun semantics and weaken audit clarity.

### Keep replay anchored to stored source files in this phase
The stored PDF and durable ingestion metadata manifest remain the replay source of truth for this phase. PostgreSQL persistence stores trusted canonical output, provenance, and audit metadata, but it does not replace source-file retention or make the persistence layer self-sufficient for source replay.

Alternative considered:
- Treat persisted canonical rows as a complete replacement for source retention: rejected because this phase is persistence for trusted ETL output, not source-archival replacement or replay decoupling.

## Risks / Trade-offs

- [A generic `canonical_pdf_record` table may need refactoring in Phase 3] -> Keep the table intentionally scoped to persistence of trusted canonical ETL output and defer ledger-specific abstractions until accounting policy is frozen.
- [Fingerprint design may overfit dataset 1 or under-deduplicate future sources] -> Build the first fingerprint from stable canonical business fields plus explicit source-system context, and document the contract as dataset-1 scoped for this change.
- [Normalization rules may evolve and change fingerprint output over time] -> Store explicit `fingerprint_version` and `canonical_schema_version` so rerun behavior remains explainable and migration choices stay visible.
- [Persisting raw and canonical payloads increases storage size] -> Accept the storage overhead for MVP because auditability and replay safety are higher priorities than early optimization.
- [Integration tests add more dependence on local PostgreSQL readiness] -> Keep unit tests focused and add only the integration tests needed to prove migrations and duplicate-safe persistence behavior.
- [Rerun semantics can be confusing if document rows are reused but import jobs are new] -> Return explicit created-versus-reused counts in the persistence result and document that import jobs are audit events while source documents are deduplicated assets.
- [A generic persistence table can become hard to query if everything becomes JSON] -> Keep a small structured surface now (`source_document_id`, `import_job_id`, `event_type`, `event_date`, `instrument_symbol`, `trade_side`, `fingerprint`, `fingerprint_version`, `canonical_schema_version`) and store the remaining canonical payload, raw values, and provenance as JSON.
- [The same business event may later be observed from multiple sources] -> Keep this change scoped to dataset 1 PDF persistence and document that multi-source reconciliation is deferred rather than implied by the current schema.

## Migration Plan

1. Confirm the persistence boundary from the PRD, roadmap, validation baseline, and ledger guidance before coding.
2. Reuse the durable ingestion metadata manifest written beside stored uploads so `storage_key` can recover source-document metadata safely.
3. Add a dedicated `app/pdf_persistence/` slice with typed schemas, persistence service, and route using `storage_key` as input.
4. Add SQLAlchemy models for `source_document`, `import_job`, and `canonical_pdf_record`, including unique constraints plus `fingerprint_version` and `canonical_schema_version`, then generate and review the first real Alembic migration.
5. Reuse the existing normalization service to obtain trusted canonical records before persistence.
6. Add deterministic document and record deduplication behavior plus transactional persistence result reporting.
7. Add focused unit coverage and PostgreSQL integration tests for first-write and rerun flows.
8. Update docs and `CHANGELOG.md` so the repo records that persistence and duplicate-safe reprocessing are implemented.

## Open Questions

- Multi-source reconciliation is intentionally deferred. In this phase, one persisted canonical record is attributed to one deduplicated source-document lineage, and later broker API coexistence will require a separate design change.
