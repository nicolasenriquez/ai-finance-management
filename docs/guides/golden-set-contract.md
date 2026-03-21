# Golden Set Contract

## Current Golden Set

Dataset 1 lives in:

- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

## Contract Principles

- The PDF is the document source of truth.
- The JSON is the expected extracted representation for regression testing.
- Extraction must preserve both raw source values and normalized typed values.
- Blank source cells become `null`.
- The pipeline must not infer missing values.

## Required Output Characteristics

Every extracted document should include:

- document metadata
- extraction metadata
- canonical column definitions
- row objects with stable `row_id`
- raw field values
- normalized field values
- provenance such as `source_page`

## Validation Expectations

Validation must compare:

- row count
- canonical columns
- raw cell values
- normalized typed values when deterministic
- page provenance where available

When mismatches happen, the report must include:

- page
- row identifier or row index
- column
- expected raw value
- actual raw value

## Persistence Implication

Golden-set processing must be idempotent:

- the same PDF must not create duplicate document records
- the same canonical rows must not create duplicate persisted records
- successful committed persistence requests must produce auditable `import_job` rows
- failed persistence attempts must not leave partial source-document, import-job, or canonical-record state
- row fingerprints or natural keys must remain stable across reruns unless the contract itself changes
- replay remains anchored to stored PDF bytes plus durable ingestion metadata manifests
- cross-source reconciliation is deferred in v1 (dataset 1 single-source contract)

## Change Management Rule

If the extraction contract changes:

1. update the PRD if scope changes
2. update this guide if the contract changes
3. update the golden set only with explicit review of the PDF and rationale
