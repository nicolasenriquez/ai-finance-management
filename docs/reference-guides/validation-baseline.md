# Validation Baseline

## Purpose

This project uses validation as a delivery gate, not as a best-effort check.

The first baseline validates the repository itself before feature work. Later baselines validate extraction correctness against golden sets.

## Repository Baseline

Expected commands:

```bash
uv run pytest -v
uv run pytest -v -m integration
uv run mypy app/
uv run pyright app/
uv run ruff check .
uv run black . --check --diff
uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium
```

Expected service checks:

```bash
curl -s http://localhost:8123/health
curl -s http://localhost:8123/health/db
curl -s http://localhost:8123/health/ready
```

Expected infrastructure checks:

```bash
docker-compose up -d db
docker-compose up -d --build
docker-compose ps
```

## Extraction Baseline

For each golden set dataset:

- run extraction
- compare against expected JSON
- generate verification report
- fail the build if required fields mismatch

## Validation Levels

### Level 1: Static Analysis, Security, and Type Safety

- Ruff
- Black
- Bandit
- MyPy
- Pyright

### Level 2: Unit Tests

- pure normalizer tests
- parser tests
- schema validation tests

### Level 3: Integration Tests

- extraction against dataset 1
- persistence flow with PostgreSQL
- API flow for upload/extract/validate
- duplicate-ingestion flow for the same PDF and same transaction set

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
