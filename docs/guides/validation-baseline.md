# Validation Baseline

## Purpose

This project uses validation as a delivery gate, not as a best-effort check.

The first baseline validates the repository itself before feature work. Later baselines validate extraction correctness against golden sets.

Current implementation status:

- dataset 1 extraction is implemented
- dataset 1 canonical normalization is implemented
- dataset 1 verification reporting is implemented
- PostgreSQL persistence and duplicate-safe reprocessing are implemented
- portfolio-ledger foundation and dataset 1 v1 accounting policy are implemented

## Repository Baseline

Expected commands:

```bash
uv run ruff check .
uv run black . --check --diff
uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high
uv run mypy app/
uv run pyright app/
uv run ty check app
uv run pytest -v
uv run pytest -v -m integration
```

Expected service checks:

```bash
curl -s http://localhost:8123/health
curl -s http://localhost:8123/health/db
curl -s http://localhost:8123/health/ready
```

Expected infrastructure checks:

```bash
# Option A: Docker Compose
docker-compose up -d db
docker-compose up -d --build
docker-compose ps

# Option B: local PostgreSQL app/service
uv run alembic upgrade head
```

## Extraction Baseline

For each golden set dataset:

- run extraction from stored upload
- run canonical normalization from stored upload
- run verification report generation from stored upload
- run persistence from stored upload
- compare verification result and mismatch evidence against expected contract
- fail the build if required fields mismatch

## Validation Levels

### Level 1: Static Analysis, Security, and Type Safety

- Ruff
- Black
- Bandit
- MyPy
- Pyright
- ty

### Level 2: Unit Tests

- pure normalizer tests
- parser tests
- schema validation tests

### Level 3: Integration Tests

- extraction against dataset 1
- persistence flow with PostgreSQL
- API flow for upload/extract/validate
- duplicate-ingestion flow for the same PDF and same transaction set
- portfolio-ledger rebuild duplicate-safety for rerun and concurrent execution

### Level 4: Manual Verification

- inspect extraction report for dataset 1
- inspect stored rows
- inspect portfolio analytics response shape

## Reporting Rule

Every major implementation phase should produce:

- validation status
- failures with concrete evidence
- next corrective action

For persistence phases, validation must also confirm:

- rerunning the same source does not create duplicate document records
- rerunning the same source does not create duplicate transaction rows
- rerunning the same canonical source does not create duplicate portfolio-ledger, lot, or lot-disposition rows
- rerunning the same source creates a new successful `import_job` row only when the full request commits
- same-hash uploads from a different `storage_key` reuse the original `source_document` row and keep first-seen metadata
- persistence replay remains anchored to stored PDFs plus ingestion metadata manifests
- v1 scope remains single-source (dataset 1 PDF); multi-source reconciliation is intentionally deferred
