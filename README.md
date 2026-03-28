# AI Finance Management

![Python](https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.120%2B-009688?logo=fastapi&logoColor=white)
![React](https://img.shields.io/badge/React-19-61DAFB?logo=react&logoColor=111)
![Vite](https://img.shields.io/badge/Vite-6-646CFF?logo=vite&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Data%20Layer-4169E1?logo=postgresql&logoColor=white)
[![CI](https://github.com/nicolasenriquez/ai-finance-management/actions/workflows/ci.yml/badge.svg)](https://github.com/nicolasenriquez/ai-finance-management/actions/workflows/ci.yml)

Contract-first personal finance analytics platform:
PDF ingestion + canonical normalization + verification + persistence + portfolio analytics API + React frontend.

![AI Finance Management Screenshot](docs/evidence/frontend/screenshots-2026-03-24/desktop-summary-first-viewport.png)

## Overview

AI Finance Management is a full-stack monorepo focused on deterministic financial data workflows.

Current product direction:

- ingest broker PDFs and source data
- normalize transactions into canonical JSON and durable records
- validate extraction against golden contracts
- expose explainable portfolio analytics APIs to the frontend

## Current Platform Status

| Area | Current Status |
|---|---|
| Phase | MVP foundation in active delivery |
| Backend | FastAPI + SQLAlchemy async |
| Frontend | React 19 + Vite 6 |
| Database | PostgreSQL |
| API Surface | 12 routes (root, health, PDF pipeline, portfolio analytics) |
| Local CLI | 30 `just` recipes (setup, DB, runtime, data-sync, quality, tests, CI, hooks) |
| CI | Secret scan + backend gates + frontend gates |
| API Docs | `/docs` + `/openapi.json` |
| Version | `0.1.0` |
| Last Verified | 2026-03-27 |

## Main Capabilities

- PDF preflight, ingestion, extraction, normalization, verification, and persistence
- ledger-first portfolio analytics (`summary` and lot-detail drill-down)
- local operator data-sync commands with explicit refresh scopes (`core`, `100`, `200`)
- strict engineering gates: lint, type checks, security scans, and tests
- structured logs and explicit fail-fast error behavior

## Architecture At a Glance

```mermaid
flowchart LR
  A[Frontend<br/>React + Vite] --> B[FastAPI API]
  B --> C[PDF Pipeline<br/>preflight -> ingest -> extract -> normalize -> verify -> persist]
  B --> D[Portfolio Analytics<br/>summary + lot detail]
  B --> E[Data Sync Service<br/>bootstrap + market refresh]
  C --> F[(PostgreSQL)]
  D --> F
  E --> F
  G[Golden Set<br/>dataset_1] --> C
```

## Core Workflow

```mermaid
flowchart TD
  S1[1. Upload PDF] --> S2[2. Preflight checks]
  S2 --> S3[3. Ingest storage + metadata]
  S3 --> S4[4. Extract deterministic tables]
  S4 --> S5[5. Normalize canonical records]
  S5 --> S6[6. Verify against golden set]
  S6 --> S7[7. Persist to PostgreSQL]
  S7 --> S8[8. Compute portfolio analytics]
  S8 --> S9[9. Render frontend views]
```

## Repository Layout

```text
.
├── app/
│   ├── core/                    # config, database, logging, middleware, health, exceptions
│   ├── pdf_preflight/
│   ├── pdf_ingestion/
│   ├── pdf_extraction/
│   ├── pdf_normalization/
│   ├── pdf_verification/
│   ├── pdf_persistence/
│   ├── portfolio_ledger/
│   ├── portfolio_analytics/
│   ├── data_sync/
│   ├── market_data/
│   ├── shared/
│   ├── golden_sets/
│   └── main.py
├── frontend/                    # React client app
│   ├── src/
│   └── scripts/
├── docs/
│   ├── product/
│   ├── guides/
│   ├── standards/
│   ├── references/
│   └── evidence/
├── scripts/                     # backend/operator CLI entrypoints
├── alembic/                     # database migrations
├── docker/                      # db initialization scripts
├── openspec/                    # change proposals/spec workflow
├── justfile                     # unified local workflow CLI
├── docker-compose.yml
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- Node.js + npm
- PostgreSQL reachable from `DATABASE_URL` (Postgres.app or Docker)
- `just` (recommended local workflow runner)

Install `just` on macOS:

```bash
brew install just
```

### Install Dependencies

```bash
cp .env.example .env
just install
```

### Configure Environment

Minimum required database URLs in `.env`:

```bash
# Runtime app DB
DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management

# Isolated test DB
TEST_DATABASE_URL=postgresql+asyncpg://<user>:<pass>@localhost:5432/ai_finance_management_test
```

YFinance operational defaults for staged refresh:

```bash
MARKET_DATA_YFINANCE_PERIOD=5y
MARKET_DATA_YFINANCE_HISTORY_FALLBACK_PERIODS=["3y","1y","6mo"]
MARKET_DATA_YFINANCE_MAX_RETRIES=1
MARKET_DATA_YFINANCE_RETRY_BACKOFF_SECONDS=0.5
MARKET_DATA_YFINANCE_REQUEST_SPACING_SECONDS=1.0
MARKET_DATA_YFINANCE_DEFAULT_CURRENCY=USD
```

### Run Locally

Ensure local PostgreSQL is already running (for example, from Postgres.app).

Run backend and frontend together:

```bash
just dev-local
```

Run full local sync first, then backend and frontend (slower):

```bash
just dev-local-sync
```

- API base: `http://localhost:8123`
- API docs: `http://localhost:8123/docs`
- Frontend: `http://localhost:3000`

Manual fallback (without `just`):

```bash
uv sync
cd frontend && npm install
uv run uvicorn app.main:app --reload --port 8123
cd frontend && npm run dev -- --port 3000
```

### Run Local Quality Gates

```bash
just backend-ci
just frontend-ci
just ci
```

## Unified CLI (`just`) Overview

- Setup / Bootstrap: `install`
- Database: `db-runtime-guard`, `db-check`, `db-upgrade`
- Local Runtime: `backend`, `frontend`, `dev`
- Data Sync Operations: `data-bootstrap-dataset1`, `market-refresh-yfinance`, `data-sync-local`, `market-symbol-universe-build`
- Code Quality: `format`, `lint`, `type`, `security`, `frontend-lint`, `frontend-type`
- Tests: `test-db-check`, `test-db-upgrade`, `test`, `test-integration`, `test-integration-heavy-100`, `frontend-test`, `frontend-build`
- Local Pre-CI Gate: `backend-ci-fast`, `backend-ci`, `frontend-ci`, `ci-fast`, `ci`
- Git Hooks: `precommit-install`, `precommit-run`, `precommit-run-prepush`

## API Surface (High-Level)

- Root:
  - `GET /`
- Health:
  - `GET /health`
  - `GET /health/db`
  - `GET /health/ready`
- PDF Pipeline:
  - `POST /api/pdf/preflight`
  - `POST /api/pdf/ingest`
  - `POST /api/pdf/extract`
  - `POST /api/pdf/normalize`
  - `POST /api/pdf/verify`
  - `POST /api/pdf/persist`
- Portfolio Analytics:
  - `GET /api/portfolio/summary`
  - `GET /api/portfolio/lots/{instrument_symbol}`

## Documentation Index

- docs home: [`docs/README.md`](docs/README.md)
- product artifacts: [`docs/product/`](docs/product)
- implementation guides: [`docs/guides/`](docs/guides)
- engineering standards: [`docs/standards/`](docs/standards)
- references and research: [`docs/references/`](docs/references)
- release history: [`CHANGELOG.md`](CHANGELOG.md)

## Golden Set

Primary extraction contract dataset:

- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

## License

MIT
