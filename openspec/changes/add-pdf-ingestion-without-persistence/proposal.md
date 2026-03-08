## Why

The repository now has PDF preflight analysis, but it still lacks the real ingestion boundary that accepts uploaded broker PDFs and routes them into the pipeline safely. This change adds that missing entry point now, while local PostgreSQL setup is temporarily blocked, so PDF ingestion can progress without expanding into persistence work yet.

## What Changes

- Add a PDF ingestion capability that accepts uploaded PDF files through FastAPI.
- Enforce request-level constraints for MIME type, file size, and page count before further processing.
- Generate deterministic upload metadata including a document identifier and SHA-256 hash.
- Store uploaded PDFs on disk in a configured safe storage path outside application source directories.
- Automatically invoke the existing PDF preflight service after a file is accepted and stored.
- Return a typed ingestion response that includes file metadata, a relative `storage_key`, and preflight status without exposing absolute filesystem paths.
- Keep this slice explicitly out of scope for database persistence, deduplication against stored records, and extraction logic.

## Capabilities

### New Capabilities
- `pdf-ingestion`: Accept, validate, hash, store, and preflight uploaded PDF files without database persistence.

### Modified Capabilities

## Impact

- Adds a new FastAPI feature slice under `app/` for PDF ingestion.
- Extends application configuration with upload limit and storage settings, starting from defaults of `10 MB` and `50` pages.
- Adds file-system based storage behavior for uploaded PDFs.
- Reuses the existing `app/pdf_preflight/` service as an internal dependency.
- Adds unit and API tests for upload validation, hashing, storage, and preflight invocation behavior.
