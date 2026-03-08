## 1. Planning

- [x] 1.1 Finalize proposal, design, and spec artifacts for the PDF preflight capability

## 2. Feature Implementation

- [x] 2.1 Add the PDF inspection dependency and create the `app/pdf_preflight/` slice with typed schemas and a preflight service
- [x] 2.2 Add a FastAPI route that accepts an `application/pdf` request body and returns the preflight extractability result

## 3. Validation

- [x] 3.1 Add unit tests for extractable, encrypted, and OCR-required PDF outcomes
- [x] 3.2 Add API tests for the preflight endpoint request and response behavior
- [x] 3.3 Run targeted lint, type, and pytest validation for the new preflight slice and update task status with the results
