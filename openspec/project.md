# Project Overview

AI Finance Management is a FastAPI + PostgreSQL application evolving into a personal finance analytics platform.

The current MVP focus is:

- ingest broker PDFs and API data
- extract transaction tables into canonical JSON
- validate the output against golden sets
- persist normalized data in PostgreSQL
- expose portfolio analytics to a future React frontend

## Product Context

Primary problems being solved:

- financial data is fragmented across multiple tools
- broker dashboards do not expose enough KPI depth
- one broker source is only available as PDF, so extraction quality must be audited carefully

The repository is also a deliberate learning vehicle for senior-level software and data engineering practice.

## Current Scope

In scope now:

- PDF ingestion and extraction
- canonical JSON normalization
- verification reports
- PostgreSQL persistence
- analytics endpoints
- grouped and lot-level frontend views

Deferred:

- authentication
- AI or agentic features
- Supabase migration
- advanced UI/UX

## Source of Truth Assets

- `docs/product/prd.md`
- `docs/product/decisions.md`
- `docs/product/roadmap.md`
- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

## Tech Stack

- Python 3.12+
- FastAPI
- PostgreSQL
- SQLAlchemy async
- Alembic
- Pydantic Settings
- structlog
- pytest
- MyPy
- Pyright
- Ruff
- Docker Compose

## Architecture

- `app/core/` for shared infrastructure
- `app/shared/` for shared utilities and schemas
- `app/golden_sets/` for extraction source-of-truth datasets
- future feature slices for ingestion, extraction, validation, persistence, and analytics

## Development Commands

```bash
uv run uvicorn app.main:app --reload --port 8123
uv run pytest -v
uv run pytest -v -m integration
uv run mypy app/
uv run pyright app/
uv run ruff check .
uv run ruff format .
docker-compose up -d db
```

## Development Rules

- Keep solutions simple and avoid premature abstractions.
- Maintain strict type safety with full annotations.
- Use Google-style docstrings.
- Follow structured logging with `domain.component.action_state`.
- Prefer contract-first development for the PDF pipeline.
- Treat golden sets as the extraction quality gate.
