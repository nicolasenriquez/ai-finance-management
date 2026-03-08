## Why

The MVP pipeline needs a deterministic preflight step before extraction so unsupported PDFs fail early with an explicit reason instead of producing ambiguous extraction behavior. This is the best near-term slice because it is product-relevant, locally scoped, and does not require persistence, normalization, or analytics work.

## What Changes

- Add a PDF preflight capability that inspects a submitted PDF before extraction.
- Detect encrypted PDFs and report them as non-extractable.
- Detect low-text or likely scanned PDFs and report that OCR would be required.
- Return a clear, typed extractability result from a dedicated preflight endpoint that a later upload flow can call automatically.
- Start with a conservative configurable text-threshold heuristic so the rule can be tuned as more broker PDFs are added.
- Add tests that cover extractable, encrypted, and OCR-required outcomes.

## Capabilities

### New Capabilities
- `pdf-preflight-analysis`: Determine whether a PDF can proceed to extraction and explain why or why not.

### Modified Capabilities

## Impact

- Adds a new PDF-focused feature slice under `app/`.
- Extends the FastAPI surface with a preflight endpoint.
- Introduces a lightweight PDF inspection dependency for encryption and text checks.
- Expands unit and API test coverage around the PDF ingestion boundary.
