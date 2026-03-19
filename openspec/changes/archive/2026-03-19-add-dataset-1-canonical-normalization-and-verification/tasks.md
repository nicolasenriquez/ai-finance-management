## 0. Investigation

- [x] 0.1 Confirm the dataset 1 canonical field expectations and verification-report evidence requirements from `app/golden_sets/dataset_1/202602_stocks.json` and the reference guides before implementation
Notes: Lock the exact canonical event types, required typed fields, blank-to-`None` behavior, and mismatch-evidence fields into tests before coding.
Notes: Confirm which fields belong in broker-specific raw payloads versus broker-agnostic canonical records so ADR-012 is preserved.
Notes: Confirmed contract anchors from `dataset_1`: `source_pdf_pages=9`, `transaction_rows=136`, `dividend_rows=34`, `split_rows=1`, and table order `compra_venta_activos`, `dividendos_recibidos`, `splits`.
Notes: Confirmed typed/raw expectations by table: trades carry `tipo` plus `{raw, usd/qty}` pairs for aporte/rescate/acciones; dividends carry `{raw, usd}` for `monto_bruto`, `monto_impuestos`, `monto_neto`; splits carry `{raw, qty}` for shares and `{raw, value}` for `ratio`.
Notes: Verified invariant expectations for trade rows in golden data: buy rows have aporte+acciones_compradas populated and rescate+acciones_vendidas null; sell rows invert that pattern; no invariant violations detected in current dataset sample.
Notes: Verification evidence requirements aligned to docs: include page provenance, row identifier (or row index when identifier is absent), field/column name, expected raw value, and actual raw value.
- [x] 0.2 Diagnose blast radius across extraction reuse, new route contracts, docs, and later persistence dependencies before implementation
Notes: Call out affected slices (`pdf_extraction`, `pdf_normalization`, `pdf_verification`), response schemas, validation commands, and downstream persistence assumptions.
Notes: Current-slice code impact map: add `app/pdf_normalization/*`, `app/pdf_verification/*`, tests under both slices, and router registration in `app/main.py`; reuse `app/pdf_extraction/service.py` via `storage_key` boundary instead of re-reading files directly.
Notes: Config and runtime blast radius is low if no new env vars are introduced; existing `api_prefix` and `pdf_upload_storage_root` settings already support the new routes and path resolution model.
Notes: Contract blast radius to manage: extraction rows always include `row_id`, but golden `splits` rows do not; verification and canonical schemas must support deterministic fallback identity (for example row index + table + source_page) to avoid reconciliation ambiguity.
Notes: Downstream dependency map: canonical field names and verification evidence shape from this change are prerequisites for Sprint 2.3 persistence keys/fingerprints and for future ledger analytics traceability; changing them later will propagate to migrations and dedup logic.
Notes: Security and trust boundaries: keep fail-fast path constraints around `storage_key` in extraction, do not add silent fallback parsing, and keep broker-specific column logic in adapters/normalizers only (ADR-012).

## 1. Contract and failing tests

- [x] 1.1 Define typed normalization and verification schemas in dedicated feature slices for canonical records, validation errors, and verification reports
Notes: Keep canonical naming broker-agnostic, preserve raw fields separately, and avoid persistence-specific identifiers in this change.
Notes: Added `app/pdf_normalization/schemas.py` with canonical record models, provenance contract, and structured normalization validation errors.
Notes: Added `app/pdf_verification/schemas.py` with verification request/result contracts, summary counts, and mismatch evidence schema.
- [x] 1.2 Add failing unit tests for dataset 1 normalization rules, including date parsing, decimal-comma parsing, blank-cell handling, and deterministic trade-direction derivation
Notes: Prefer pure normalizer tests for parser behavior and focused fixtures for invalid row combinations.
Notes: Added fail-first unit tests in `app/pdf_normalization/tests/test_service.py` for date parsing, decimal-comma parsing, blank-cell normalization, and deterministic/ambiguous trade-side derivation.
- [x] 1.3 Add failing service or API tests for successful normalization, explicit validation failures, successful verification, and mismatch evidence reporting
Notes: Reuse stored-upload `storage_key` inputs and keep PostgreSQL out of scope for all tests in this change.
Notes: Added fail-first service tests in `app/pdf_normalization/tests/test_service.py` for successful dataset normalization and explicit invalid-row rejection.
Notes: Added fail-first service tests in `app/pdf_verification/tests/test_service.py` for successful verification and mismatch-evidence reporting.

## 2. Normalization feature slice

- [x] 2.1 Create `app/pdf_normalization/service.py` to reuse extraction output and map dataset 1 rows into typed canonical records with preserved raw values and provenance
Notes: Added `app/pdf_normalization/service.py` with `normalize_pdf_from_storage()` that reuses `extract_pdf_from_storage()`, preserves deterministic table/row emission order, and maps trades/dividends/splits into typed canonical records.
Notes: Normalization output preserves `raw_values` plus provenance (`table_name`, `row_id`, `row_index`, `source_page`) and reports deterministic summary counts expected by dataset 1 (`136/34/1`).
- [x] 2.2 Implement row-level validation and fail-fast error handling for ambiguous or invalid canonical mappings
Notes: Enforce invariants such as blank-to-`None`, typed parsing, and deterministic event-type derivation only when the source row supports it explicitly.
Notes: Added fail-fast parsing/validation helpers (`parse_date_value`, `parse_decimal_comma_value`, `derive_trade_side`, required-field guards) that raise structured `PdfNormalizationClientError` with `NormalizationValidationError` evidence.
Notes: Date parsing now tolerates extraction whitespace artifacts (for example `2023- 09-25`) while still enforcing ISO ordering and explicit rejection for invalid dates/numbers or ambiguous trade-side combinations.
- [x] 2.3 Add `app/pdf_normalization/routes.py` and register the router in `app/main.py` using `storage_key` as the request boundary
Notes: Keep the route thin and return explicit 4xx behavior for invalid keys or normalization failures.
Notes: Added `app/pdf_normalization/routes.py` (`POST /pdf/normalize` under configured API prefix) and router registration in `app/main.py`, following existing extraction-style request logging and 4xx translation semantics.

## 3. Verification feature slice

- [x] 3.1 Create `app/pdf_verification/service.py` to compare normalized dataset 1 output against the golden set and compute deterministic summary counts
Notes: Added `app/pdf_verification/service.py` with `verify_pdf_from_storage()` that reuses normalization output and compares it against the checked-in dataset 1 golden contract (`app/golden_sets/dataset_1/202602_stocks.json`) without database access.
Notes: Summary counts are deterministic (`expected_records`, `actual_records`, `mismatch_count`) and verification status is explicit `passed`/`failed`, with fail-fast rejection when normalization cannot produce trusted records.
- [x] 3.2 Emit machine-readable mismatch evidence with row or record identifiers, field names, expected values, actual values, and provenance where available
Notes: The report should be diff-friendly and stable enough to serve as the later validation baseline artifact.
Notes: Implemented deterministic mismatch generation in `build_verification_report()` with `VerificationMismatch` entries including `table_name`, `row_id` fallback behavior, `row_index`, `source_page`, `field`, and expected/actual raw values.
Notes: Record pairing uses deterministic identity (`table_name` + `row_index` + `source_page`) so golden rows that omit `row_id` (notably `splits`) still reconcile reliably with normalized output.
- [x] 3.3 Add `app/pdf_verification/routes.py` and register the router in `app/main.py` so verification can run from a stored upload without database access
Notes: Added `app/pdf_verification/routes.py` (`POST /pdf/verify` under configured API prefix) and registered router in `app/main.py`, mirroring existing thin-route + explicit 4xx translation pattern.

## 4. Validation and documentation

- [x] 4.1 Run targeted validation with `uv run pytest -v app/pdf_normalization/tests app/pdf_verification/tests`, `uv run mypy app/`, `uv run pyright app/`, `uv run ruff check .`, `uv run black . --check --diff`, and `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium`
Notes: Integration DB tests are not required unless the implementation unexpectedly crosses into persistence.
Notes: Validation evidence completed: targeted normalization+verification tests passed, strict MyPy and Pyright returned zero errors, Ruff and Black gates passed, and Bandit reported no medium/high findings.
Notes: To satisfy strict typing gates, verification and normalization fail-first tests were updated with explicit typed casts and verification schemas/service type hints were tightened without altering runtime behavior.
- [x] 4.2 Update affected docs and delivery history, including extraction and validation reference guides plus `CHANGELOG.md`, to record that canonical normalization and verification are implemented while persistence remains pending
Notes: Updated `docs/reference-guides/pdf-extraction-guide.md` to mark canonical normalization (`/pdf/normalize`) and verification (`/pdf/verify`) as implemented downstream slices, while keeping persistence and deduplication explicitly pending.
Notes: Updated `docs/reference-guides/validation-baseline.md` to reflect the current dataset 1 canonical baseline (extraction + normalization + verification implemented; persistence validation pending).
Notes: Added `2026-03-19` changelog entries documenting canonical slice delivery, validation evidence, and the explicit persistence boundary.
Notes: `openspec validate --specs --all` confirms this change spec passes, but global spec validation still fails on pre-existing `pdf-ingestion` and `pdf-preflight-analysis` spec files missing required `## Purpose` sections.
