## Context

The repository now has a standalone PDF preflight endpoint in `app/pdf_preflight/`, but there is still no ingestion boundary that accepts uploaded files and routes them through that capability. The PRD and backlog require PDF uploads to validate MIME, size, and page count, compute SHA-256 hashes, and store original PDFs safely before extraction begins. For this change, local PostgreSQL setup is intentionally unavailable, so the ingestion slice must stay fully functional without database persistence, deduplication checks, or Alembic work.

## Goals / Non-Goals

**Goals:**
- Add a dedicated `app/pdf_ingestion/` feature slice that accepts PDF uploads through FastAPI.
- Enforce configured MIME, byte-size, and page-count limits before continuing the pipeline.
- Compute deterministic upload metadata including document ID and SHA-256 hash.
- Store accepted PDFs on disk under a configured storage root outside application source paths.
- Invoke the existing PDF preflight service automatically and return its result together with ingestion metadata.
- Keep validation runnable without Docker or PostgreSQL by relying on unit and API tests only.

**Non-Goals:**
- Persisting documents or metadata in PostgreSQL.
- Enforcing duplicate detection against prior uploads.
- Running extraction, normalization, reconciliation, or analytics.
- Supporting non-PDF file types or OCR fallback behavior.

## Decisions

### Use a dedicated `app/pdf_ingestion/` feature slice
The ingestion boundary is a feature concern, not a shared utility, so it should own its route, schemas, service, and tests in a separate vertical slice. This keeps file-upload behavior independent from `app/pdf_preflight/` while still allowing reuse of the preflight service.

Alternative considered:
- Extend `app/pdf_preflight/` to handle uploads directly: rejected because it would mix transport, storage, and extractability concerns into one slice.

### Accept multipart uploads with `UploadFile`
The user-facing ingestion path should receive PDFs as multipart file uploads because that matches the PRD’s “upload a PDF statement” requirement and maps cleanly to browser clients. The route should read bytes once, then pass those bytes through validation, hashing, storage, and preflight.

Alternative considered:
- Reuse raw `application/pdf` request bodies: rejected because it is less ergonomic for real upload flows and duplicates the role of the existing preflight endpoint.

### Enforce limits through configuration and validate in-memory before storing
The service should read the uploaded bytes, reject oversized files early, inspect page count from the in-memory PDF, and only write the file after validation succeeds. Config should cover upload storage root, max byte size, and max page count so local development can change limits without code edits.

Alternative considered:
- Save first and validate afterward: rejected because it would leave invalid files on disk and complicate cleanup behavior.

### Store PDFs on disk using generated document IDs, not original filenames
Accepted files should be stored under a configured root such as `.data/pdf_uploads/` using a generated document ID and fixed `.pdf` extension. The response can still include the original filename, but the filesystem name should avoid unsafe characters, collisions, and path traversal issues.

Alternative considered:
- Store using the original filename: rejected because filenames are not unique or trustworthy.

### Expose only a relative storage key in the API response
The ingestion response should include a relative `storage_key` derived from the configured storage root, but it should not expose the absolute on-disk path. This keeps the response portable across machines and environments while still giving callers a stable identifier for later debugging or persistence work. If local debugging needs the full path, it can be recorded in structured logs instead.

Alternative considered:
- Return the absolute stored path in the API response: rejected because it leaks local filesystem details and couples the API contract to one machine layout.

### Return a typed ingestion result that nests preflight output
The route should return one response model that includes document metadata and the existing preflight result. This keeps the upload boundary useful immediately without forcing clients to call two endpoints or reconstruct state from multiple responses.

Alternative considered:
- Return only a storage acknowledgment and require a second preflight request: rejected because the current goal is to automatically reuse preflight as part of ingestion.

### Start with conservative default upload limits of 10 MB and 50 pages
The ingestion settings should ship with defaults of `10 MB` for file size and `50` pages for page count until more broker samples justify recalibration. These values are intentionally conservative for a local single-user MVP, but they remain configurable through settings so implementation does not hard-code them permanently.

Alternative considered:
- Choose stricter defaults immediately: rejected because the current golden-set sample does not justify aggressively low limits and early false rejections would slow iteration.

### Keep this slice explicitly independent from the database
Even though the long-term MVP requires PostgreSQL persistence, this slice should not import `get_db`, define models, or add migrations. The document ID and SHA-256 hash are still useful now, and they preserve a clean future handoff to persistence work later.

Alternative considered:
- Block implementation until Docker/PostgreSQL is available: rejected because it would stall a valid earlier MVP slice that can be built and tested independently.

## Risks / Trade-offs

- [Files stored only on disk are not yet queryable or deduplicated] -> Return metadata needed for future persistence and keep the storage contract simple so a later persistence slice can adopt it.
- [Reading full uploads into memory limits scalability] -> Accept this trade-off for the current single-user MVP and enforce conservative max-byte settings through configuration.
- [Page-count validation depends on `pypdf` parsing behavior] -> Treat malformed PDFs as request errors and cover limits with focused tests.
- [Storage path defaults may be misconfigured] -> Validate the configured root on write and keep it outside source-code directories by default.

## Migration Plan

1. Add ingestion-related settings to `app.core.config` and `.env.example`.
2. Create `app/pdf_ingestion/` with typed schemas, service logic, routes, and tests.
3. Wire the new router into `app.main`.
4. Validate unit and API behavior for acceptance, rejection, hashing, storage, and automatic preflight.
5. Defer persistence integration to a later change that can attach database models and deduplication rules to the same document metadata contract.
