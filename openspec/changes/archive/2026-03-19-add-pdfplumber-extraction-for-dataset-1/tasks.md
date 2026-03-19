## 0. Investigation

- [x] 0.1 Confirm dataset 1 table shape and failure modes from the golden set PDF and JSON before implementation
Notes: Lock the expected columns, row order, repeated-header behavior, footer patterns, and provenance expectations into tests first.
Notes: Golden set confirms three table groups and summary counts in `app/golden_sets/dataset_1/202602_stocks.json`: `compra_venta_activos` (136), `dividendos_recibidos` (34), and `splits` (1), with `source_pdf_pages=9`.
Notes: Provenance expectations are explicit per row (`source_page`) and ordered `row_id` sequences; extraction tests should assert these before implementation.
Notes: Primary failure modes to encode in tests come from docs plus dataset shape: repeated headers, footer artifacts, locale comma decimals, and blank/null cell handling.

## 1. Contract and test baseline

- [x] 1.1 Add `pdfplumber` to the project dependencies and define typed extraction schemas in `app/pdf_extraction/schemas.py`
Notes: Keep the schema raw-only for this change; normalization and canonical parsing remain out of scope until Sprint 1 Item 1.4.
Notes: Added `pdfplumber` in `pyproject.toml` and created raw extraction contracts in `app/pdf_extraction/schemas.py` (`request`, `result`, `table`, `row`).
- [x] 1.2 Add failing tests for dataset 1 extraction output, repeated-header removal, footer filtering, and `source_page` provenance
Notes: Prefer service-level tests using the checked-in golden set plus focused fixtures that isolate one edge case at a time.
Notes: Added fail-first service tests in `app/pdf_extraction/tests/test_service.py` for summary counts, header/footer filtering, and row provenance.
Notes: Current proof intentionally fails until task 2.1 provides `app.pdf_extraction.service.extract_pdf_from_storage`.

## 2. Extraction feature slice

- [x] 2.1 Create `app/pdf_extraction/service.py` to open stored PDFs with `pdfplumber`, iterate relevant tables across pages, and emit deterministic raw rows
Notes: Preserve source order and generate stable `row_id` values in emission order.
Notes: Added `extract_pdf_from_storage()` with deterministic table ordering, row emission, and source-page provenance in `app/pdf_extraction/service.py`.
- [x] 2.2 Implement explicit filtering for repeated headers and dataset 1 footer artifacts while failing clearly when no supported table shape is found
Notes: Keep filtering deterministic and narrow; do not infer missing values or silently return partial data.
Notes: Added explicit repeated-header and footer-artifact filtering plus fail-fast `422` when expected dataset tables are not found.
- [x] 2.3 Add `app/pdf_extraction/routes.py` and register the router in `app/main.py` to extract from an existing stored upload via `storage_key`
Notes: Keep the route thin, resolve the file under the configured upload root, and return explicit 4xx errors for missing stored files.
Notes: Added `/api/pdf/extract` route in `app/pdf_extraction/routes.py`, registered router in `app/main.py`, and added route tests for success/missing file/path traversal.

## 3. Validation and delivery evidence

- [x] 3.1 Run targeted validation with `uv run pytest -v app/pdf_extraction/tests`, `uv run mypy app/`, `uv run pyright app/`, and `uv run ruff check .`
Notes: Integration DB tests are not required unless the implementation unexpectedly crosses into persistence or database setup.
Notes: Validation results: `pytest app/pdf_extraction/tests` (6 passed), `mypy app/` (pass), `pyright app/` (0 errors), `ruff check .` (pass).
- [x] 3.2 Update `CHANGELOG.md` and any affected extraction contract docs to record the new raw extraction capability and its current scope limits
Notes: Make the delivery history explicit that this slice adds raw extraction only, with normalization and persistence still pending.
Notes: Added extraction delivery entry in `CHANGELOG.md` and updated `docs/reference-guides/pdf-extraction-guide.md` with implemented scope and current limits.
