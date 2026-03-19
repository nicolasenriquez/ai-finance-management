## Why

The repo now supports PDF ingestion and preflight, but the pipeline still stops before any table data is extracted from the broker statement. Sprint 1 Item 1.3 is the next required slice because dataset 1 needs deterministic raw row extraction before normalization, validation, or persistence can proceed.

## What Changes

- Add a PDF extraction capability that uses `pdfplumber` as the primary engine for dataset 1.
- Extract row-wise raw table data from the ingested broker PDF across multiple pages.
- Remove repeated table headers and obvious footer artifacts from extracted output.
- Preserve source page provenance for every emitted row.
- Keep extraction output raw and deterministic, without normalization, canonical mapping, persistence, or analytics logic.
- Add focused tests for multi-page extraction behavior using dataset 1 and fixture-driven edge cases.

## Capabilities

### New Capabilities
- `pdf-extraction`: Extract deterministic raw transaction-table rows from supported text-based broker PDFs using `pdfplumber`.

### Modified Capabilities

## Impact

- Adds a new feature slice under `app/` for PDF extraction.
- Introduces `pdfplumber`-driven extraction logic and typed extraction response models.
- Extends test coverage around the ETL spine using dataset 1 as the extraction contract.
- Prepares the codebase for the later normalization, verification, and persistence slices without coupling this change to the database.
