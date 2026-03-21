# PDF Extraction Guide

## Objective

Build a deterministic pipeline that converts broker PDFs into canonical JSON suitable for validation and persistence.

## Current Implementation Status (Sprints 1.3-2.4)

- Implemented endpoint: `POST /api/pdf/extract`
- Input boundary: stored `storage_key` under configured upload root
- Engine: `pdfplumber`
- Implemented table outputs for dataset 1:
  - `compra_venta_activos`
  - `dividendos_recibidos`
  - `splits`
- Implemented behavior:
  - deterministic table and row emission order
  - repeated-header removal
  - footer artifact filtering
  - per-row `source_page` provenance
  - explicit fail-fast errors for missing storage files, invalid keys, and unsupported extraction shapes
- Downstream canonical validation slices now implemented on top of extraction:
  - `POST /api/pdf/normalize`
  - `POST /api/pdf/verify`
  - `POST /api/pdf/persist`
  - deterministic canonical mapping and typed parsing for dataset 1
  - machine-readable mismatch evidence against golden set
  - PostgreSQL persistence with deterministic fingerprints and duplicate-safe reruns
- Explicitly not in current scope:
  - ledger and analytics APIs
  - multi-source canonical reconciliation across independent ingestion systems

## Primary Strategy

- use `pdfplumber` as the first extraction engine
- treat the PDF as the source of truth
- preserve raw values exactly
- normalize only in a separate parsing layer
- validate output against a golden set before and during persistence

## Pipeline Stages

Stages 1-3 are implemented in ingestion/preflight/extraction. Stages 4-6 are implemented in
dedicated normalization and verification slices. Stage 7 persistence is also implemented.

### 1. Ingest

- accept only PDF uploads
- enforce file size and page-count limits
- store the file safely
- generate a SHA-256 hash

### 2. Preflight

- detect encryption
- determine whether the PDF is text-based or likely scanned
- fail clearly when OCR would be required and OCR support is not enabled

### 3. Extract

- iterate page by page
- identify target tables
- remove repeated headers
- remove footer artifacts
- preserve page provenance

### 4. Map

- normalize source headers
- map headers to canonical field names
- keep the mapping layer explicit so column order changes do not break downstream logic

### 5. Parse

- preserve raw strings
- normalize decimals with comma separators
- normalize money values
- normalize dates
- convert empty values to `None`

### 6. Emit

- produce deterministic JSON
- preserve ordering or define stable sort rules explicitly
- record engine and extraction metadata

### 7. Persist

- persist deduplicated `source_document` metadata using SHA-256 identity
- create `import_job` rows only for successful committed persistence requests
- insert canonical records with deterministic versioned fingerprints and skip duplicates safely
- keep replay anchored to stored PDF bytes plus durable ingestion metadata manifests

## Common Blind Spots

- repeated headers on every page
- multi-line asset names
- shifted columns caused by blank cells
- footer rows being parsed as data
- locale-specific decimal parsing
- invisible glyph or encoding artifacts

## Design Rules

- do not infer missing values
- do not mix extraction and normalization logic
- do not persist unvalidated extraction output as trusted data
- pin extraction settings so reruns are explainable
