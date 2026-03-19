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
- basic grouped-table frontend

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

- [`docs/prd.md`](docs/prd.md)
- [`docs/backlog-sprints.md`](docs/backlog-sprints.md)
- [`docs/roadmap.md`](docs/roadmap.md)
- [`docs/decisions.md`](docs/decisions.md)
- [`docs/references.md`](docs/references.md)

Reference guides:

- [`docs/reference-guides/golden-set-contract.md`](docs/reference-guides/golden-set-contract.md)
- [`docs/reference-guides/pdf-extraction-guide.md`](docs/reference-guides/pdf-extraction-guide.md)
- [`docs/reference-guides/validation-baseline.md`](docs/reference-guides/validation-baseline.md)

Engineering standards:

- [`docs/ruff-standard.md`](docs/ruff-standard.md)
- [`docs/black-standard.md`](docs/black-standard.md)
- [`docs/bandit-standard.md`](docs/bandit-standard.md)
- [`docs/mypy-standard.md`](docs/mypy-standard.md)
- [`docs/pyright-standard.md`](docs/pyright-standard.md)
- [`docs/pytest-standard.md`](docs/pytest-standard.md)

## Quick Start

```bash
cp .env.example .env
uv sync
docker-compose up -d db
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --port 8123
```

API docs: `http://localhost:8123/docs`

## Validation Commands

```bash
uv run pytest -v
uv run pytest -v -m integration
uv run mypy app/
uv run pyright app/
uv run ruff check .
uv run black . --check --diff
uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium
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
