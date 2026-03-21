## 0. Investigation

- [ ] 0.1 Confirm the minimum persistence contract for dataset 1 from the PRD, roadmap, validation baseline, and ledger guidance before implementation
Notes: Lock the exact persistence boundary for this slice: deduplicated source documents, import-job audit rows, canonical-record storage, duplicate-safe reruns, and explicit non-goals around ledger analytics.
Notes: Confirm the exact fingerprint input for each dataset 1 event type and which provenance fields must remain audit-only metadata.
- [ ] 0.2 Confirm the resolved design decisions for success-only `import_job` rows, verification-as-validation-only, and first-seen source-document metadata before coding
Notes: Ensure the implementation does not reintroduce the previous ambiguity around failed-attempt auditing, runtime verification requirements, or duplicate-upload metadata mutation.
- [ ] 0.3 Diagnose blast radius across migrations, database models, routes, validation commands, and later ledger dependencies before coding
Notes: Call out affected slices (`app/core/database.py`, new `app/pdf_persistence/*`, `alembic/versions/*`, integration tests, docs, and `CHANGELOG.md`) and confirm whether any existing ETL contracts need to change.
Notes: Explicitly verify that this change should reuse the existing `storage_key`, durable ingestion metadata manifest, and normalization boundary rather than creating a parallel persistence input contract.

## 1. Contract and failing tests

- [ ] 1.1 Define typed persistence request/response schemas and error contracts for document reuse, record insert counts, duplicate skips, and successful import-job identifiers
Notes: Keep the API boundary thin and typed, and make created-versus-reused behavior explicit so reruns remain understandable.
- [ ] 1.2 Add failing unit tests for deterministic fingerprint generation, duplicate-detection behavior, and persistence result accounting
Notes: Prefer pure tests around fingerprint helpers and summary/result logic before wiring PostgreSQL.
- [ ] 1.3 Add failing integration or route tests for first persistence, duplicate-safe reruns, and rollback on failed persistence
Notes: Cover document reuse, canonical-record skip-on-duplicate behavior, and the fail-fast requirement that a failed persistence request leaves no partial import state behind.

## 2. Persistence models and migrations

- [ ] 2.1 Add SQLAlchemy models for `source_document`, `import_job`, and `canonical_pdf_record` with timestamps, foreign keys, uniqueness constraints, and JSON payload/provenance storage
Notes: Keep the schema persistence-oriented and avoid freezing final ledger table design in this change.
Notes: Store a small structured query surface on `canonical_pdf_record` (`source_document_id`, `event_type`, `event_date`, `instrument_symbol`, `fingerprint`) and keep the rest of the canonical payload, raw values, and provenance in JSON.
- [ ] 2.2 Generate and review the first real Alembic migration for the persistence schema
Notes: Confirm unique constraints for document hash and canonical record fingerprint plus rollback behavior before moving to service implementation.
- [ ] 2.3 Add any supporting persistence helpers needed for deterministic upsert-or-skip behavior
Notes: Keep helpers local to the persistence slice unless they become shared across three or more features.

## 3. Persistence feature slice

- [ ] 3.1 Create `app/pdf_persistence/service.py` to reuse normalization output, resolve or create the source document, create an import job, and persist missing canonical records transactionally
Notes: The service should reuse trusted normalization, compute deterministic fingerprints, and commit only when the full persistence flow succeeds.
- [ ] 3.2 Add `app/pdf_persistence/routes.py` and register the router in `app/main.py` using `storage_key` as the persistence request boundary
Notes: Keep route logic thin and return explicit client or server failures rather than silent fallbacks.
- [ ] 3.3 Return a typed persistence result that distinguishes created documents, reused documents, inserted records, and skipped duplicates
Notes: The response should make rerun semantics auditable and easy to validate in tests.

## 4. Validation and documentation

- [ ] 4.1 Run targeted and integration validation with `uv run pytest -v app/pdf_persistence/tests`, `docker-compose up -d db`, `uv run alembic upgrade head`, `uv run pytest -v -m integration`, `uv run mypy app/`, `uv run pyright app/`, `uv run ty check app`, `uv run ruff check .`, `uv run black . --check --diff`, and `uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high`
Notes: Persistence is the first slice that must prove migration and PostgreSQL-backed rerun behavior, so integration validation is required here.
- [ ] 4.2 Update affected docs and delivery history, including persistence-related reference guidance and `CHANGELOG.md`, to record that PostgreSQL persistence and duplicate-safe reprocessing are implemented
Notes: Reflect the new persistence boundary in repo guidance and capture any remaining workflow gaps, including the pre-existing OpenSpec spec-validation issue if it still exists after implementation.
