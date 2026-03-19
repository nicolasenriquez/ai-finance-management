## Why

The repository now ingests PDFs, runs preflight, and extracts deterministic raw rows for dataset 1, but it still stops before producing trusted canonical records. The next change is needed now because normalization and verification are the minimum contract required before persistence, deduplication, and later portfolio analytics can be implemented safely.

## What Changes

- Add a canonical normalization layer for dataset 1 extracted tables that preserves raw values while producing typed canonical fields.
- Add schema validation for normalized rows so malformed or ambiguous records fail fast before any later persistence work.
- Add deterministic verification reporting against the dataset 1 golden set with row-level and field-level mismatch evidence.
- Keep this slice explicitly out of scope for PostgreSQL persistence, transaction deduplication, ledger modeling, and analytics APIs.

## Capabilities

### New Capabilities
- `pdf-normalization`: Normalize dataset 1 extracted rows into canonical, broker-agnostic records with raw values, typed values, and provenance preserved.
- `pdf-verification`: Reconcile normalized dataset 1 output against the golden set and emit a deterministic machine-readable verification report.

### Modified Capabilities
- None.

## Impact

- Affected code: new normalization and verification slices plus focused updates to extraction-adjacent contracts and tests.
- Affected APIs/contracts: canonical JSON and verification-report response or artifact contracts for dataset 1.
- Affected docs: PRD-adjacent reference guides, backlog tracking, and `CHANGELOG.md`.
- Dependencies/systems: no new external service dependency is required; PostgreSQL remains out of scope for this change.
