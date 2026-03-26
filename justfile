set shell := ["bash", "-euo", "pipefail", "-c"]

# Default entrypoint: show available recipes.
default:
    @just --list

# -----------------------------------------------------------------------------
# Setup / Bootstrap
# -----------------------------------------------------------------------------

# Install backend and frontend dependencies.
install:
    uv sync
    cd frontend && npm install

# -----------------------------------------------------------------------------
# Database
# -----------------------------------------------------------------------------

# Guard local runtime from accidentally pointing at a test database.
db-runtime-guard:
    #!/usr/bin/env bash
    set -euo pipefail

    raw_url="${DATABASE_URL:-}"
    if [[ -z "$raw_url" ]] && [[ -f .env ]]; then
      raw_url="$(grep -E '^[[:space:]]*DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      raw_url="${raw_url%\"}"
      raw_url="${raw_url#\"}"
      raw_url="${raw_url%\'}"
      raw_url="${raw_url#\'}"
    fi

    if [[ -z "$raw_url" ]]; then
      echo "DATABASE_URL is not set. Export it or define DATABASE_URL in .env."
      exit 1
    fi

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    if [[ -n "$test_url" ]] && [[ "$raw_url" == "$test_url" ]]; then
      echo "DATABASE_URL and TEST_DATABASE_URL resolve to the same value."
      echo "Refusing to start runtime with shared dev/test database."
      exit 1
    fi

    runtime_db_name="${raw_url##*/}"
    runtime_db_name="${runtime_db_name%%\?*}"
    if [[ "$runtime_db_name" == *_test ]]; then
      echo "Refusing to run app against test database: ${runtime_db_name}"
      exit 1
    fi

    echo "Runtime DB guard passed: ${runtime_db_name}"

# Verify PostgreSQL is reachable using DATABASE_URL (env or .env).
db-check:
    #!/usr/bin/env bash
    set -euo pipefail

    choose_pg_isready() {
      local candidate=""

      if [[ -n "${PG_ISREADY_BIN:-}" ]]; then
        if [[ ! -x "${PG_ISREADY_BIN}" ]]; then
          echo "PG_ISREADY_BIN is set but not executable: ${PG_ISREADY_BIN}" >&2
          return 1
        fi
        echo "${PG_ISREADY_BIN}"
        return 0
      fi

      if command -v pg_isready >/dev/null 2>&1; then
        candidate="$(command -v pg_isready)"
        if "${candidate}" --version >/dev/null 2>&1; then
          echo "${candidate}"
          return 0
        fi
      fi

      candidate="/Applications/Postgres.app/Contents/Versions/latest/bin/pg_isready"
      if [[ -x "${candidate}" ]] && "${candidate}" --version >/dev/null 2>&1; then
        echo "${candidate}"
        return 0
      fi

      shopt -s nullglob
      for candidate in /Applications/Postgres.app/Contents/Versions/*/bin/pg_isready; do
        if [[ -x "${candidate}" ]] && "${candidate}" --version >/dev/null 2>&1; then
          echo "${candidate}"
          shopt -u nullglob
          return 0
        fi
      done
      shopt -u nullglob

      echo "No working pg_isready binary found. Install PostgreSQL client tools or set PG_ISREADY_BIN." >&2
      return 1
    }

    raw_url="${DATABASE_URL:-}"
    if [[ -z "$raw_url" ]] && [[ -f .env ]]; then
      raw_url="$(grep -E '^[[:space:]]*DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      raw_url="${raw_url%\"}"
      raw_url="${raw_url#\"}"
      raw_url="${raw_url%\'}"
      raw_url="${raw_url#\'}"
    fi

    if [[ -z "$raw_url" ]]; then
      echo "DATABASE_URL is not set. Export it or define DATABASE_URL in .env."
      exit 1
    fi

    # Convert SQLAlchemy-style URLs (postgresql+asyncpg://...) into libpq URLs.
    pg_url="$(printf '%s' "$raw_url" | sed -E 's#^postgresql\\+[^:]+://#postgresql://#')"
    pg_isready_bin="$(choose_pg_isready)"
    "${pg_isready_bin}" -d "$pg_url"

# Apply all pending Alembic migrations.
db-upgrade:
    #!/usr/bin/env bash
    set -euo pipefail

    uv run alembic upgrade head

    # Self-heal drift where alembic_version is at head but schema tables are missing.
    if ! uv run python - <<'PY'
import asyncio
import sys
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from app.core.config import get_settings

REQUIRED_TABLES = (
    "source_document",
    "import_job",
    "canonical_pdf_record",
    "portfolio_transaction",
    "dividend_event",
    "corporate_action_event",
    "lot",
    "lot_disposition",
    "market_data_snapshot",
    "price_history",
)


async def main() -> int:
    engine = create_async_engine(get_settings().database_url)
    try:
        async with engine.connect() as conn:
            missing_tables: list[str] = []
            for table_name in REQUIRED_TABLES:
                exists = (
                    await conn.execute(
                        text("SELECT to_regclass(:regclass_name)"),
                        {"regclass_name": f"public.{table_name}"},
                    )
                ).scalar_one()
                if exists is None:
                    missing_tables.append(table_name)

            if missing_tables:
                print(
                    "Alembic drift detected: missing tables at current revision: "
                    + ", ".join(missing_tables),
                    file=sys.stderr,
                )
                return 1
            return 0
    finally:
        await engine.dispose()


raise SystemExit(asyncio.run(main()))
PY
    then
      echo "Alembic drift detected (missing tables at current revision). Re-stamping and re-applying migrations."
      uv run alembic stamp base
      uv run alembic upgrade head
    fi

# -----------------------------------------------------------------------------
# Local Runtime
# -----------------------------------------------------------------------------

# Run backend only (FastAPI + reload on port 8123).
backend:
    uv run uvicorn app.main:app --reload --port 8123

# Run frontend only (Vite on port 3000).
frontend:
    cd frontend && npm run dev -- --port 3000

# Run full local stack:
# 1) DB readiness check
# 2) DB migrations
# 3) backend + frontend in parallel
# Stops both processes when either exits or on Ctrl+C.
dev: db-runtime-guard db-check db-upgrade
    #!/usr/bin/env bash
    backend_pid=0
    frontend_pid=0

    cleanup() {
      local exit_code=$?
      if [[ "$backend_pid" -ne 0 ]] && kill -0 "$backend_pid" 2>/dev/null; then
        kill "$backend_pid" 2>/dev/null || true
      fi
      if [[ "$frontend_pid" -ne 0 ]] && kill -0 "$frontend_pid" 2>/dev/null; then
        kill "$frontend_pid" 2>/dev/null || true
      fi
      wait "$backend_pid" 2>/dev/null || true
      wait "$frontend_pid" 2>/dev/null || true
      exit "$exit_code"
    }

    trap cleanup EXIT INT TERM

    uv run uvicorn app.main:app --reload --port 8123 &
    backend_pid=$!
    (
      cd frontend
      npm run dev -- --port 3000
    ) &
    frontend_pid=$!

    echo "Backend running on http://localhost:8123"
    echo "Frontend running on http://localhost:3000"

    command_status=0
    while true; do
      if ! kill -0 "$backend_pid" 2>/dev/null; then
        wait "$backend_pid" || command_status=$?
        break
      fi
      if ! kill -0 "$frontend_pid" 2>/dev/null; then
        wait "$frontend_pid" || command_status=$?
        break
      fi
      sleep 1
    done

    exit "$command_status"

# -----------------------------------------------------------------------------
# Data Sync Operations
# -----------------------------------------------------------------------------

# Run dataset_1 bootstrap (ingest -> persist -> rebuild).
# Optional override: `just data-bootstrap-dataset1 <dataset_pdf_path>`.
data-bootstrap-dataset1 dataset_pdf_path="": db-check db-upgrade
    #!/usr/bin/env bash
    if [[ -n "{{dataset_pdf_path}}" ]]; then
      uv run python -m scripts.data_sync_operations data-bootstrap-dataset1 --dataset-pdf-path "{{dataset_pdf_path}}"
    else
      uv run python -m scripts.data_sync_operations data-bootstrap-dataset1
    fi

# Run yfinance supported-universe refresh.
# Optional overrides: `just market-refresh-yfinance <snapshot_captured_at_iso8601> <refresh_scope>`.
market-refresh-yfinance snapshot_captured_at="" refresh_scope="": db-check db-upgrade
    #!/usr/bin/env bash
    args=()
    if [[ -n "{{snapshot_captured_at}}" ]]; then
      args+=(--snapshot-captured-at "{{snapshot_captured_at}}")
    fi
    if [[ -n "{{refresh_scope}}" ]]; then
      args+=(--refresh-scope "{{refresh_scope}}")
    fi
    uv run python -m scripts.data_sync_operations market-refresh-yfinance "${args[@]}"

# Run local sync in strict order: bootstrap first, then market refresh.
# Optional overrides: `just data-sync-local <dataset_pdf_path> <snapshot_captured_at_iso8601> <refresh_scope>`.
data-sync-local dataset_pdf_path="" snapshot_captured_at="" refresh_scope="": db-check db-upgrade
    #!/usr/bin/env bash
    args=()
    if [[ -n "{{dataset_pdf_path}}" ]]; then
      args+=(--dataset-pdf-path "{{dataset_pdf_path}}")
    fi
    if [[ -n "{{snapshot_captured_at}}" ]]; then
      args+=(--snapshot-captured-at "{{snapshot_captured_at}}")
    fi
    if [[ -n "{{refresh_scope}}" ]]; then
      args+=(--refresh-scope "{{refresh_scope}}")
    fi
    uv run python -m scripts.data_sync_operations data-sync-local "${args[@]}"

# Build versioned market-data symbol universe (required portfolio + starter 100/200).
# Optional overrides: `just market-symbol-universe-build <dataset_json_path> <output_path>`.
market-symbol-universe-build dataset_json_path="" output_path="":
    #!/usr/bin/env bash
    if [[ -n "{{dataset_json_path}}" ]] && [[ -n "{{output_path}}" ]]; then
      uv run python -m scripts.build_market_symbol_universe --dataset-json-path "{{dataset_json_path}}" --output-path "{{output_path}}"
    elif [[ -n "{{dataset_json_path}}" ]]; then
      uv run python -m scripts.build_market_symbol_universe --dataset-json-path "{{dataset_json_path}}"
    elif [[ -n "{{output_path}}" ]]; then
      uv run python -m scripts.build_market_symbol_universe --output-path "{{output_path}}"
    else
      uv run python -m scripts.build_market_symbol_universe
    fi

# -----------------------------------------------------------------------------
# Code Quality
# -----------------------------------------------------------------------------

# Auto-fix lint findings when possible and format Python code.
format:
    uv run ruff check . --fix
    uv run black .

# Read-only style and format gate.
lint:
    uv run ruff check .
    uv run black . --check --diff

# Strict typing gate (all three checkers must pass).
type:
    uv run mypy app/
    uv run pyright app/
    uv run ty check app

# Security gate for source and dependencies.
security:
    uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high
    uv run pip-audit --progress-spinner=off --ignore-vuln CVE-2026-4539

# Frontend static lint gate (TypeScript compile).
frontend-lint:
    cd frontend && npm run lint

# Frontend type checking.
frontend-type:
    cd frontend && npm run type-check

# -----------------------------------------------------------------------------
# Tests
# -----------------------------------------------------------------------------

# Verify test DB URL is configured and isolated from runtime DATABASE_URL.
test-db-check:
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    if [[ -z "$test_url" ]]; then
      echo "TEST_DATABASE_URL is not set. Add it to .env or export it before running tests."
      exit 1
    fi

    runtime_url="${DATABASE_URL:-}"
    if [[ -z "$runtime_url" ]] && [[ -f .env ]]; then
      runtime_url="$(grep -E '^[[:space:]]*DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      runtime_url="${runtime_url%\"}"
      runtime_url="${runtime_url#\"}"
      runtime_url="${runtime_url%\'}"
      runtime_url="${runtime_url#\'}"
    fi

    if [[ -n "$runtime_url" ]] && [[ "$test_url" == "$runtime_url" ]]; then
      echo "TEST_DATABASE_URL must differ from DATABASE_URL."
      exit 1
    fi

    test_db_name="${test_url##*/}"
    test_db_name="${test_db_name%%\?*}"
    echo "Test DB check passed: ${test_db_name}"

# Apply migrations to the isolated test database.
test-db-upgrade: test-db-check
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    DATABASE_URL="$test_url" uv run alembic upgrade head

# Run unit and non-integration tests.
test: test-db-check
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    DATABASE_URL="$test_url" uv run pytest -v -m "not integration"

# Run integration tests only.
test-integration: test-db-upgrade
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    DATABASE_URL="$test_url" uv run pytest -v -m "integration and not market_scope_heavy and not market_scope_very_heavy"

# Run heavy integration tests only (scope-100 refresh).
test-integration-heavy-100: test-db-upgrade
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    DATABASE_URL="$test_url" uv run pytest -v -m "integration and market_scope_heavy"

# Run very-heavy integration tests only (scope-200 refresh).
test-integration-heavy-200: test-db-upgrade
    #!/usr/bin/env bash
    set -euo pipefail

    test_url="${TEST_DATABASE_URL:-}"
    if [[ -z "$test_url" ]] && [[ -f .env ]]; then
      test_url="$(grep -E '^[[:space:]]*TEST_DATABASE_URL=' .env | tail -n 1 | cut -d '=' -f2- || true)"
      test_url="${test_url%\"}"
      test_url="${test_url#\"}"
      test_url="${test_url%\'}"
      test_url="${test_url#\'}"
    fi

    DATABASE_URL="$test_url" uv run pytest -v -m "integration and market_scope_very_heavy"

# Frontend unit tests.
frontend-test:
    cd frontend && npm run test

# Frontend production build verification.
frontend-build:
    cd frontend && npm run build

# -----------------------------------------------------------------------------
# Local Pre-CI Gate
# -----------------------------------------------------------------------------

# Fast backend pre-CI gate (no integration tests).
backend-ci-fast: lint type security test

# Backend pre-CI gate.
backend-ci: backend-ci-fast test-integration

# Frontend pre-CI gate.
frontend-ci: frontend-lint frontend-type frontend-test frontend-build

# Local fast CI-equivalent gate for quick confidence before commit.
ci-fast: backend-ci-fast frontend-ci

# Local full CI-equivalent gate for pre-push/PR confidence.
# Runs full backend + frontend gates, then the most complete pre-push hook stage.
ci: backend-ci frontend-ci precommit-run-prepush

# -----------------------------------------------------------------------------
# Git Hooks
# -----------------------------------------------------------------------------

# Install git hooks for commit + push validation.
precommit-install:
    uvx --from pre-commit python -m pre_commit install
    uvx --from pre-commit python -m pre_commit install --hook-type pre-push

# Run all configured hooks across the repository.
precommit-run:
    uvx --from pre-commit python -m pre_commit run --all-files

# Run pre-push stage hooks across the repository (e.g., gitleaks, push-time checks).
precommit-run-prepush:
    uvx --from pre-commit python -m pre_commit run --all-files --hook-stage pre-push
