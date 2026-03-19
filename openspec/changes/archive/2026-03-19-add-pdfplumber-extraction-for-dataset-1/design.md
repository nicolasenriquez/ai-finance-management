## Context

The repository now has two earlier ETL slices in place: PDF ingestion stores accepted files on disk and returns a `storage_key`, and PDF preflight determines whether extraction can proceed. The next backlog step is to turn those accepted PDFs into deterministic raw row output for dataset 1 using `pdfplumber`, while keeping normalization, validation reporting, and PostgreSQL persistence out of scope for this change.

The golden set in `app/golden_sets/dataset_1/202602_stocks.json` already establishes the target table shape and shows that repeated headers, footer artifacts, and page provenance matter for correctness. The implementation therefore needs a narrow extraction boundary that can consume the existing stored-upload contract and return testable raw output without inventing broker-specific normalization rules too early.

## Goals / Non-Goals

**Goals:**
- Add a dedicated `app/pdf_extraction/` feature slice with typed schemas, extraction service, route, and tests.
- Use `pdfplumber` as the primary extraction engine for dataset 1 text PDFs.
- Extract multi-page transaction tables from stored uploaded PDFs identified by `storage_key`.
- Remove repeated header rows and obvious footer artifacts deterministically.
- Preserve row order, stable row identifiers, and `source_page` provenance in the raw extraction result.
- Fail explicitly when the stored PDF is missing or when no supported table shape can be extracted.

**Non-Goals:**
- Canonical mapping or field normalization.
- Schema validation or verification-report generation.
- PostgreSQL models, migrations, or deduplicated persistence.
- OCR, image-based parsing, or secondary extraction engines.
- Broker-agnostic generalization beyond what dataset 1 requires today.

## Decisions

### Use a dedicated `app/pdf_extraction/` feature slice
Extraction is a feature concern with its own schemas, service, route, and tests. Keeping it in a separate slice preserves the repo’s vertical-slice architecture and avoids leaking extraction rules into `app/core/`, `app/shared/`, or the existing ingestion/preflight slices.

Alternative considered:
- Extend `app/pdf_ingestion/` to perform extraction directly: rejected because it would mix file acceptance/storage concerns with table parsing concerns and make later normalization harder to reason about.

### Use `storage_key` as the application boundary for extraction
The current ingestion flow already stores accepted PDFs under a configured upload root and returns a relative `storage_key`. The extraction route should accept that key, resolve it under the configured root, and delegate parsing to the extraction service. This keeps the ETL spine connected without introducing database lookups or forcing clients to re-upload the same file.

Alternative considered:
- Accept raw PDF uploads again for extraction: rejected because it duplicates ingestion behavior and breaks the intended handoff between ETL stages.

### Extract page-by-page with `pdfplumber` and emit raw rows only
The service should open the stored PDF with `pdfplumber`, iterate pages in source order, collect relevant table rows, and return raw string values plus minimal metadata such as `row_id`, `source_page`, and extraction engine details. Normalization and canonical mapping remain separate concerns for Sprint 1 Item 1.4.

Alternative considered:
- Normalize values during extraction: rejected because it mixes extraction and parsing concerns and makes regressions harder to isolate.

### Filter repeated headers and footer artifacts with explicit deterministic rules
Dataset 1 already tells us the primary failure modes: repeated headers across pages and footer rows that are not transactions. The service should apply narrow row filters based on exact header matches and dataset-specific footer patterns before emitting rows. If no supported table shape is found after filtering, the service should fail explicitly instead of returning partial or ambiguous output.

Alternative considered:
- Add fuzzy heuristics or inferred cleanup rules: rejected because this first extraction slice needs explainable and reproducible behavior, not clever guessing.

### Start with golden-set-backed tests before implementation details
Because extraction bugs are easy to hide in complex PDFs, the first implementation step should lock the expected behavior with tests that compare row counts, key raw values, filtered headers, filtered footers, and `source_page` provenance against dataset 1 and focused fixtures. The implementation can then stay minimal while still meeting the fail-fast and TDD-first rules in `AGENTS.md`.

Alternative considered:
- Implement the parser first and backfill tests later: rejected because it weakens the repository’s required TDD discipline on the riskiest part of the ETL spine so far.

## Risks / Trade-offs

- [Dataset 1 filtering rules may be too narrow for future broker statements] -> Keep the first implementation intentionally scoped to dataset 1 and isolate filtering logic so later changes can widen support explicitly.
- [Table extraction can vary across `pdfplumber` settings] -> Pin the initial extraction approach in one service and lock behavior with golden-set tests before tuning.
- [Using `storage_key` couples extraction to the ingestion storage contract] -> Accept this for the current ETL spine because it avoids duplicate uploads and still keeps database persistence out of scope.
- [A thin route adds transport work on top of parsing] -> Keep the route minimal and push all parsing behavior into the service so the extra surface area stays small.

## Migration Plan

1. Add the `pdfplumber` dependency to the project.
2. Create `app/pdf_extraction/` with typed schemas, service logic, route, and tests.
3. Register the extraction router in `app.main`.
4. Validate extraction behavior against dataset 1 and focused fixture cases for header/footer filtering and provenance.
5. Update affected docs and changelog entries so the repo history clearly distinguishes raw extraction from later normalization and persistence work.

## Open Questions

None for current scope.
