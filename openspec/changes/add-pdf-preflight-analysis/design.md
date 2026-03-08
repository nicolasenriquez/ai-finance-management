## Context

The current codebase contains only shared infrastructure, health endpoints, and tests for those shared systems. Product docs define a PDF ETL pipeline where preflight comes immediately after ingestion and before extraction. This change should stay narrowly focused on deciding extractability, without adding upload persistence, OCR, extraction, or database coupling.

## Goals / Non-Goals

**Goals:**
- Add a typed service that accepts PDF bytes and returns an explicit extractability status.
- Distinguish between extractable text PDFs, encrypted PDFs, and likely scanned/low-text PDFs.
- Expose a small FastAPI route that future ingestion flows can call.
- Keep the result deterministic and easy to test with in-memory fixtures.

**Non-Goals:**
- Supporting OCR or decryption.
- Persisting uploaded files or preflight reports.
- Running extraction, normalization, reconciliation, or database writes.
- Introducing broker-specific logic.

## Decisions

### Use a dedicated `app/pdf_preflight/` feature slice
This matches the repo’s intended vertical-slice architecture and keeps PDF-specific behavior out of `app/core/` and `app/shared/`. The slice should own its schemas, service, routes, and tests.

Alternative considered:
- Place the logic in `app/shared/`: rejected because preflight is still a feature concern, not a utility reused by 3+ features.

### Use a lightweight PDF inspection library rather than the extraction engine
Preflight only needs to answer two questions: is the file encrypted, and is there enough extractable text to proceed. A lightweight library such as `pypdf` is enough for this and avoids prematurely coupling the preflight layer to the extraction implementation.

Alternative considered:
- Use `pdfplumber` immediately: rejected because it is a better fit for extraction than for this narrow preflight check.

### Return unsupported extractability as a typed success response, not an HTTP error
Encrypted and OCR-required documents are valid preflight outcomes, not server failures. The route should return a 200 response with a machine-readable status and explanation. Malformed uploads remain request errors.

Alternative considered:
- Return 4xx for encrypted or scanned PDFs: rejected because the document itself can be valid while still unsupported by the current pipeline.

### Detect likely scanned PDFs using extracted text density
The first implementation should count extracted non-whitespace characters across pages and treat anything below a conservative configurable threshold of 20 characters as OCR-required. This keeps the heuristic simple, deterministic, and easy to test while leaving room to tune it later from configuration.

Alternative considered:
- Add image-density or OCR probing heuristics: rejected as unnecessary scope for the first implementation.

### Keep preflight callable as a dedicated endpoint and automatic inside the future upload flow
This slice should expose an explicit preflight endpoint now because it is the simplest way to validate and debug the capability independently. When secure upload is implemented later, that flow should invoke the same service automatically before extraction begins.

Alternative considered:
- Require clients to call preflight as a mandatory separate step forever: rejected because it adds avoidable friction to the main MVP workflow.

## Risks / Trade-offs

- [Short text PDFs may be flagged too aggressively] -> Keep the threshold conservative and expose diagnostic metadata such as page count and extracted text character count.
- [Odd PDFs may not expose text consistently through one library] -> Keep the service boundary small so heuristics can evolve without changing the API contract.
- [Future upload flow may prefer an internal service call instead of multipart input] -> Design the service around raw bytes and keep the route as a thin transport adapter.

## Migration Plan

1. Add the PDF inspection dependency.
2. Create the `app/pdf_preflight/` feature slice with schemas, service, and route.
3. Register the route in `app.main`.
4. Add unit and API tests using in-memory PDFs for each extractability status.
5. Validate with targeted lint, type, and pytest commands before broader validation.

## Open Questions

- The initial 20-character threshold is intentionally conservative and may still need calibration once more broker PDFs are available.
