# AI Finance Management

Personal finance analytics application built with FastAPI and PostgreSQL, designed to evolve from a contract-first PDF/data ingestion pipeline into a full analytics product.

Current MVP direction:

- ingest broker PDFs and API data
- normalize transactions into canonical JSON + database records
- validate extraction against golden sets
- expose analytics APIs for a React frontend

## Current Focus

The active MVP does **not** include authentication or AI features yet.

In scope now:

- PDF upload and extraction
- canonical transaction JSON generation
- verification against golden sets
- PostgreSQL persistence
- KPI and portfolio analytics
- frontend MVP with grouped instrument summary, lot-detail drill-down, and dual-theme support

Deferred:

- auth and user management
- GenAI features, agents, and enrichment
- advanced UI/UX polish
- Supabase migration

## Golden Set

The first extraction contract lives in:

- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

This dataset is the initial source of truth for the PDF extraction pipeline.

## Documentation

Start here:

- [`docs/README.md`](docs/README.md)
- [`docs/product/prd.md`](docs/product/prd.md)
- [`docs/product/frontend-mvp-prd-addendum.md`](docs/product/frontend-mvp-prd-addendum.md)
- [`docs/product/backlog-sprints.md`](docs/product/backlog-sprints.md)
- [`docs/product/roadmap.md`](docs/product/roadmap.md)
- [`docs/product/decisions.md`](docs/product/decisions.md)
- [`docs/references/references.md`](docs/references/references.md)
- [`docs/references/frontend-references.md`](docs/references/frontend-references.md)

Reference guides:

- [`docs/guides/golden-set-contract.md`](docs/guides/golden-set-contract.md)
- [`docs/guides/pdf-extraction-guide.md`](docs/guides/pdf-extraction-guide.md)
- [`docs/guides/validation-baseline.md`](docs/guides/validation-baseline.md)
- [`docs/guides/frontend-architecture-guide.md`](docs/guides/frontend-architecture-guide.md)
- [`docs/guides/frontend-api-and-ux-guide.md`](docs/guides/frontend-api-and-ux-guide.md)
- [`docs/guides/frontend-design-system-guide.md`](docs/guides/frontend-design-system-guide.md)
- [`docs/guides/frontend-delivery-checklist.md`](docs/guides/frontend-delivery-checklist.md)
- [`docs/guides/postgres-local-setup.md`](docs/guides/postgres-local-setup.md)
- [`docs/guides/postgres-performance-guide.md`](docs/guides/postgres-performance-guide.md)
- [`docs/guides/postgres-security-guide.md`](docs/guides/postgres-security-guide.md)
- [`docs/guides/pgvector-guide.md`](docs/guides/pgvector-guide.md)
- [`docs/guides/timescaledb-guide.md`](docs/guides/timescaledb-guide.md)

Engineering standards:

- [`docs/standards/ruff-standard.md`](docs/standards/ruff-standard.md)
- [`docs/standards/black-standard.md`](docs/standards/black-standard.md)
- [`docs/standards/bandit-standard.md`](docs/standards/bandit-standard.md)
- [`docs/standards/frontend-standard.md`](docs/standards/frontend-standard.md)
- [`docs/standards/ty-standard.md`](docs/standards/ty-standard.md)
- [`docs/standards/mypy-standard.md`](docs/standards/mypy-standard.md)
- [`docs/standards/pyright-standard.md`](docs/standards/pyright-standard.md)
- [`docs/standards/pytest-standard.md`](docs/standards/pytest-standard.md)
- [`docs/standards/postgres-standard.md`](docs/standards/postgres-standard.md)

## Quick Start

```bash
cp .env.example .env
uv sync
docker-compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8123
```

API docs: `http://localhost:8123/docs`

Frontend MVP:

```bash
docker-compose up -d frontend
```

Frontend URL: `http://localhost:5173`

## Validation Commands

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

## Architecture

Current structure:

```text
app/
├── core/                    # Shared infrastructure
├── shared/                  # Shared schemas and utilities
├── golden_sets/             # Source-of-truth datasets for extraction validation
└── main.py                  # FastAPI entry point
```

Target MVP architecture:

```text
backend (FastAPI) + db (PostgreSQL) + frontend (React)
```

All three services will run via `docker-compose` in local development.

## Tech Stack

- Python 3.12+
- FastAPI
- SQLAlchemy async
- PostgreSQL 18
- Alembic
- Pydantic Settings
- structlog
- pytest
- MyPy
- Pyright
- Ruff
- Black
- Bandit
- Docker Compose

## License

MIT
