## 1. Configuration and contract setup

- [x] 1.1 Add ingestion settings in `app/core/config.py` and `.env.example` for storage root, max upload bytes, and max page count with defaults of `10 MB` and `50` pages
- [x] 1.2 Define typed ingestion request/response schemas in `app/pdf_ingestion/schemas.py`, including document metadata, a relative `storage_key`, and nested preflight output

## 2. Ingestion feature slice

- [x] 2.1 Create `app/pdf_ingestion/service.py` to read uploaded bytes, validate MIME and byte-size limits, compute SHA-256, inspect page count, and write accepted PDFs to the configured storage root using generated document IDs
- [x] 2.2 Add `app/pdf_ingestion/routes.py` with a multipart upload endpoint that calls the ingestion service and returns explicit client errors for invalid uploads
- [x] 2.3 Register the PDF ingestion router in `app/main.py` and keep it independent from database sessions, models, and migrations

## 3. Validation

- [x] 3.1 Add unit tests for hashing, page-count validation, generated storage filenames, and rejection of invalid or oversized uploads
- [x] 3.2 Add API tests covering successful upload, automatic preflight invocation, non-PDF rejection, and over-page-limit rejection
- [x] 3.3 Run targeted validation for the new slice with `uv run pytest -v app/pdf_ingestion/tests`, `uv run mypy app/`, and `uv run ruff check .`, then record any remaining gaps caused by unavailable Docker/PostgreSQL

Validation note: No Docker/PostgreSQL gap was encountered because this ingestion slice is filesystem and preflight only.
