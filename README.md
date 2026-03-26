# AI Finance Management

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120%2B-009688?logo=fastapi&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-4169E1?logo=postgresql&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
[![CI](https://github.com/nicolasenriquez/ai-finance-management/actions/workflows/ci.yml/badge.svg)](https://github.com/nicolasenriquez/ai-finance-management/actions/workflows/ci.yml)

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
- [`docs/guides/local-workflow-justfile.md`](docs/guides/local-workflow-justfile.md)
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

Recommended prerequisites:

- Python 3.12+
- Node.js + npm
- PostgreSQL reachable from `DATABASE_URL` (Postgres.app or Docker)
- `just` (recommended local workflow runner)

Install `just` on macOS:

```bash
brew install just
```

Bootstrap dependencies:

```bash
cp .env.example .env
just install
```

Configure separate development and test databases in `.env`:

```bash
# Runtime app DB (used by just dev / backend)
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management

# Isolated test DB (used by just test / just test-integration)
TEST_DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management_test
```

If you use Docker for local PostgreSQL:

```bash
docker-compose up -d db
```

Run backend + frontend together:

```bash
just dev
```

API docs: `http://localhost:8123/docs`
Frontend URL: `http://localhost:3000`

Manual fallback (without `just`):

```bash
uv sync
cd frontend && npm install
uv run uvicorn app.main:app --reload --port 8123
cd frontend && npm run dev -- --port 3000
```

## Validation Commands

```bash
just backend-ci
just frontend-ci
just ci
just test-integration
just precommit-run
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

Current local workflow:

- backend + frontend: `just dev`
- database: Docker Compose (`docker-compose up -d db`) or local PostgreSQL app

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
