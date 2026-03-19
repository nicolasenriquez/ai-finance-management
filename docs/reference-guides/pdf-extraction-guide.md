# PDF Extraction Guide

## Objective

Build a deterministic pipeline that converts broker PDFs into canonical JSON suitable for validation and persistence.

## Current Implementation Status (Sprint 1.3)

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
- Explicitly not in current slice:
  - canonical field mapping
  - numeric/date normalization
  - schema validation reporting
  - persistence

## Primary Strategy

- use `pdfplumber` as the first extraction engine
- treat the PDF as the source of truth
- preserve raw values exactly
- normalize only in a separate parsing layer
- validate output against a golden set before persistence

## Pipeline Stages

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
