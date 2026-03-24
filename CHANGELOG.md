# Changelog

All notable changes to this repository are documented here.

This changelog is designed for both human readers and AI agents.
Entries must remain concise, factual, and structured.

## Entry Format

Use this structure for new entries:

```md
## YYYY-MM-DD

### <type>(<scope>): <short title>
- Summary: <what changed>
- Why: <intent/business or engineering reason>
- Files: <key files/areas>
- Validation: <tests/checks run, or blocked reason>
- Notes: <optional constraints/follow-up>
```

`type` guidance: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## 2026-03-23

## 2026-03-24

### feat(frontend-ui): add dual-theme portfolio analytics polish pass and derived overview hierarchy
- Summary: Upgraded the React frontend shell with a user-selectable light/dark theme, stronger semantic design tokens, overview cards for summary and lot-detail screens, row-level drill-down affordances, and more intentional responsive/error-state presentation.
- Why: The initial frontend scaffold matched the documented MVP structure but still felt like a bootstrap pass; this change brings the shipped UI closer to the documented frontend quality bar for Phase 5 without introducing unsupported analytics.
- Files: `frontend/src/app/**`, `frontend/src/components/**`, `frontend/src/features/**`, `frontend/src/pages/**`, `CHANGELOG.md`.
- Validation: `npm run test` (5 tests passed across theme and overview suites), `npm run build` (pass, Vite production bundle generated).

### docs(frontend-ui): align frontend guidance with dual-theme tokens and shipped UX hierarchy
- Summary: Updated the frontend design-system, architecture, delivery checklist, standard, and product addendum to document dual-theme parity requirements, overview-card hierarchy, and the MVP boundary for restrained theme switching.
- Why: The implementation now includes a real theme layer and stronger page composition rules; the docs need to describe those behaviors explicitly so the code and delivery checklists remain aligned.
- Files: `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-architecture-guide.md`, `docs/guides/frontend-delivery-checklist.md`, `docs/standards/frontend-standard.md`, `docs/product/frontend-mvp-prd-addendum.md`, `CHANGELOG.md`.
- Validation: Documentation reviewed against the updated frontend implementation and existing frontend roadmap/quality documents.

### feat(frontend-bootstrap): add React MVP scaffold with typed API boundary and Docker Compose dev service
- Summary: Added the initial `frontend/` application scaffold using React, TypeScript, Vite, React Router, TanStack Query, Zod, and decimal.js, including portfolio summary and lot-detail pages, shared state components, a typed analytics API client, and a Docker Compose frontend dev service.
- Why: Turn the new frontend architecture and UX documentation into an executable MVP foundation so implementation can proceed against the ledger-only analytics contract without inventing structure during delivery.
- Files: `frontend/**`, `docker-compose.yml`, `.env.example`, `.gitignore`, `CHANGELOG.md`.
- Validation: Architecture and API contract reviewed against `docs/guides/frontend-architecture-guide.md`, `docs/guides/frontend-api-and-ux-guide.md`, and `app/portfolio_analytics`; runtime validation executed later in 2026-03-24 frontend UI follow-up (`npm run test`, `npm run build`).

### docs(frontend-architecture): add concrete MVP frontend architecture guide
- Summary: Added a dedicated frontend architecture guide that defines the recommended MVP stack, folder structure, layering model, component boundaries, API boundary strategy, decimal-safe finance handling, and server-state/UI-state testing approach.
- Why: The repository already had frontend product, UX, design-system, and quality documents; this change adds the missing technical bridge between those decisions and executable implementation work.
- Files: `docs/guides/frontend-architecture-guide.md`, `docs/README.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against `docs/product/frontend-mvp-prd-addendum.md`, `docs/guides/frontend-api-and-ux-guide.md`, `docs/guides/frontend-design-system-guide.md`, and `docs/standards/frontend-standard.md`.

### docs(frontend-roadmap): upgrade phase 5 from screen delivery to quality-gated frontend foundation and MVP hardening
- Summary: Expanded the frontend roadmap and sprint backlog so frontend work now explicitly covers design-system foundation, API-to-UI contract locking, decimal-safe finance formatting, accessibility/performance quality gates, and evidence-based release hardening in addition to the summary and lot-detail screens.
- Why: The repository now has a much stronger frontend documentation baseline than the old roadmap reflected; planning needed to catch up so Phase 5 measures real frontend quality instead of only container setup and page existence.
- Files: `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against `docs/product/frontend-mvp-prd-addendum.md`, `docs/guides/frontend-api-and-ux-guide.md`, `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-delivery-checklist.md`, and `docs/standards/frontend-standard.md`.

### feat(portfolio-analytics): add ledger-backed portfolio summary and lot-detail APIs
- Summary: Implemented the new `portfolio_analytics` feature slice with typed response schemas, read-only analytics services derived from persisted ledger truth, and FastAPI routes for grouped summary and lot-detail drill-down.
- Why: Deliver the Phase 4 backend contract required for the frontend MVP while preserving ledger-first, fail-fast analytics boundaries and deferring market-data-dependent valuation.
- Files: `app/portfolio_analytics/{__init__.py,schemas.py,service.py,routes.py,tests/*}`, `app/main.py`, `docs/product/roadmap.md`, `docs/guides/portfolio-ledger-and-analytics-guide.md`, `docs/guides/validation-baseline.md`, `openspec/changes/add-portfolio-analytics-api-from-ledger/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests` (7 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_analytics app/main.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_analytics --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run alembic stamp base` + `UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (applied locally for integration-test schema).
- Notes: v1 analytics remain intentionally ledger-only (`open_*`, `realized_*`, `dividend_*`, `as_of_ledger_at`); valuation and unrealized market metrics stay deferred until market-data phases.

### fix(portfolio-ledger): make rebuild state-convergent under canonical corrections and source drift
- Summary: Updated ledger rebuild to clear previously derived lot state before recomputation, upsert derived event rows on canonical-record conflicts, and prune stale derived event rows no longer present in the source document canonical set.
- Why: Ensure `rebuild_portfolio_ledger_from_canonical_records` converges to current canonical truth instead of preserving stale rows from earlier runs.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors).
- Notes: Integration tests for new rebuild regressions could not run in this sandbox because PostgreSQL socket access is blocked (`PermissionError: [Errno 1] Operation not permitted`); run them in a DB-enabled environment.

### fix(docker-local): restore compose defaults compatible with existing postgres_data volumes
- Summary: Switched Docker Compose and `.env.example` defaults back to legacy-compatible `postgres:postgres` credentials while keeping `POSTGRES_APP_*` overrides available for dedicated app-role local setups.
- Why: Prevent local startup breakage for developers with existing `postgres_data` volumes where init scripts do not rerun.
- Files: `docker-compose.yml`, `.env.example`, `CHANGELOG.md`.
- Validation: Configuration update reviewed for variable resolution and compatibility with existing local volume behavior.

### fix(portfolio-ledger): align rebuild convergence with event-type migration and moved-source lot cleanup
- Summary: Changed stale-event pruning to be event-type aware (trade/dividend/split canonical IDs tracked independently) and added a post-upsert lot-state cleanup pass so moved-in transactions do not retain stale lot dispositions.
- Why: Prevent contradictory derived rows when canonical records change event families and ensure lot/disposition truth converges after source-ownership drift corrections.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_ledger/tests -m "not integration"` (15 passed, 10 deselected).
- Notes: New integration regressions require a migrated PostgreSQL test database; local run currently fails early with `UndefinedTableError: relation "source_document" does not exist` until `uv run alembic upgrade head` is applied to the active DB.

## 2026-03-22

### docs(roadmap): add deferred database-hardening phase and version-constraint note
- Summary: Updated the roadmap and backlog to state that the current local PostgreSQL baseline uses separated bootstrap and app credentials today while stricter runtime hardening remains deferred until software-version constraints can be revisited.
- Why: Keep planning artifacts aligned with the implemented local baseline and avoid pretending full PostgreSQL hardening is already complete.
- Files: `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against the accepted PostgreSQL security posture and current local runtime constraints.

### docs(database-ops): add local PostgreSQL setup guide and formalize database posture ADR
- Summary: Added a PostgreSQL local setup guide for `.env`, Docker Compose, migrations, and health checks, and recorded the local-first but security-bounded database posture as an accepted ADR.
- Why: Keep local onboarding practical while making the project’s database operating model and security boundary explicit before future hosted or shared environments are introduced.
- Files: `docs/guides/postgres-local-setup.md`, `docs/guides/postgres-security-guide.md`, `docs/product/decisions.md`, `docs/README.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current `.env.example`, `docker-compose.yml`, and the existing PostgreSQL standards and security guides.

### feat(local-postgres): split bootstrap and runtime credentials in Docker local baseline
- Summary: Replaced the insecure `postgres:postgres` local default with explicit admin and app credential variables, mounted a first-boot init script that creates the application role and database, and updated the app container to connect with the dedicated runtime role.
- Why: Align the local baseline with the documented least-privilege direction without making local onboarding impractical.
- Files: `docker-compose.yml`, `.env.example`, `docker/db/init/01-create-app-role.sh`, `docs/guides/postgres-local-setup.md`, `docs/guides/postgres-security-guide.md`, `docs/product/decisions.md`, `CHANGELOG.md`.
- Validation: Configuration review pending runtime verification; expected checks are `docker-compose config`, first-boot database initialization, `uv run alembic upgrade head`, and health endpoint validation.

### docs(database-security): add PostgreSQL security guide and harden database standard
- Summary: Added a dedicated PostgreSQL security guide and expanded the PostgreSQL standard with security baseline rules covering authentication, least-privilege roles, network exposure, TLS expectations, privilege hygiene, and security-sensitive features.
- Why: The repository already documented application-code security with Bandit, but lacked a database-specific security posture for PostgreSQL setup and future shared or remote environments.
- Files: `docs/guides/postgres-security-guide.md`, `docs/standards/postgres-standard.md`, `docs/README.md`, `docs/references/references.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current PostgreSQL 18 documentation plus the provided Tiger Data security references, with PostgreSQL 7.0 explicitly treated as historical unsupported context.

### docs(database): add PostgreSQL standard and optional extension guides
- Summary: Added a repository PostgreSQL standard plus focused guides for performance investigation, `pgvector`, and TimescaleDB adoption, and linked them from the main documentation indexes and references.
- Why: Formalize how database schema, migrations, indexing, and extension choices should be handled without mixing core PostgreSQL rules with optional future features.
- Files: `docs/standards/postgres-standard.md`, `docs/guides/postgres-performance-guide.md`, `docs/guides/pgvector-guide.md`, `docs/guides/timescaledb-guide.md`, `docs/README.md`, `docs/references/references.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current repository schema/query patterns and official PostgreSQL, `pgvector`, and Tiger Data documentation.

### feat(portfolio-ledger): close phase 3 ledger foundation and accounting-policy freeze for dataset 1
- Summary: Completed ledger-foundation closeout by fixing fractional lot-basis precision propagation, finalizing strict typing/lint compliance in ledger tests, and adding a fractional buy/sell integration regression for cent-consistent FIFO basis behavior.
- Why: Lock a trustworthy, explicit portfolio-ledger and accounting-policy contract before Phase 4 analytics APIs and frontend work.
- Files: `app/portfolio_ledger/{service.py,accounting.py,schemas.py,tests/test_policy_schemas.py,tests/test_rebuild_integration.py,tests/test_canonical_mapping.py,tests/test_models_schema.py,tests/test_fifo_accounting.py,tests/fixtures/dataset_1_v1_finance_cases.json}`, `docs/product/roadmap.md`, `docs/guides/portfolio-ledger-and-analytics-guide.md`, `docs/guides/validation-baseline.md`, `openspec/changes/add-ledger-foundation-and-accounting-policy-for-dataset-1/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 3 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (3 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_ledger --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger` (pass), `openspec validate --specs --all` (this change passes; pre-existing failures remain in `spec/pdf-ingestion` and `spec/pdf-preflight-analysis`).
- Notes: Product and guide docs now explicitly record that Phase 3 is ledger/accounting foundation only; market-data valuation and analytics endpoints remain deferred to later phases.

### fix(portfolio-ledger): preserve residual lot basis cents across partial sells and correct open-lot summary count
- Summary: Updated sell-side lot mutation logic to carry remaining lot basis by subtraction (with close-lot residual allocation) instead of recomputing from unit basis, and changed rebuild summary `open_lots` to count only lots with positive remaining quantity.
- Why: Prevent realized-basis drift from repeating-decimal unit costs and keep rebuild/log output semantically accurate for open positions.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_fractional_three_partial_sells_preserves_basis_and_open_lot_count` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 4 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (4 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(portfolio-ledger): order same-day lot events by canonical sequence across split and trade records
- Summary: Replaced the hard-coded same-day trade-before-split lot event ordering with canonical-record ordering so same-day split/trade histories are applied in persisted canonical order.
- Why: Prevent false FIFO insufficient-lot failures and miscomputed lot state when a same-day split must precede a same-day sell.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_same_day_split_before_sell_uses_canonical_event_order` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (5 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 5 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(portfolio-ledger): enforce explicit rebuild transactions after session autobegin
- Summary: Updated rebuild transaction handling to clear implicit `AUTOBEGIN` state before ledger writes and always run writes inside an explicit `begin()` or `begin_nested()` scope, with an integration regression for pre-read/autobegin sessions.
- Why: Prevent rebuild persistence from depending on unrelated prior session reads and guarantee local commit/rollback ownership for the rebuild path.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_autobegin_session_still_commits_ledger_writes` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (6 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 6 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(validation): clear pyright unknown-type route helper and restore black formatting gate
- Summary: Added explicit JSON payload narrowing in the persistence route test helper and restored Black-compliant spacing in the persistence schema migration module.
- Why: Close repository validation failures (`pyright app/` unknown member/type usage and `black --check` formatting drift) without changing runtime behavior.
- Files: `app/pdf_persistence/tests/test_routes.py`, `alembic/versions/c8b0721b0977_add_pdf_persistence_schema.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run black . --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass).

### fix(portfolio-ledger): isolate implicit session transactions and reject non-finite canonical decimals
- Summary: Replaced the rebuild path’s implicit-transaction rollback with an isolated-session execution path for `AUTOBEGIN` state (preserving caller transaction state), and tightened canonical decimal coercion to reject non-finite values (`NaN`, `Infinity`, `-Infinity`) with deterministic 422 errors.
- Why: Prevent silent caller transaction mutation/data loss while keeping duplicate-safe reruns functional, and enforce finance-safe numeric semantics before lot math executes.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `app/portfolio_ledger/tests/test_canonical_mapping.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (pass after local schema reset), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (15 passed, 6 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (6 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger alembic/env.py alembic/versions/12ecb9689094_add_portfolio_ledger_foundation_tables.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger alembic/env.py alembic/versions/12ecb9689094_add_portfolio_ledger_foundation_tables.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_ledger --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger` (pass).

## 2026-03-21

### feat(pdf-persistence): persist canonical dataset 1 records in PostgreSQL with duplicate-safe reruns
- Summary: Implemented `pdf_persistence` end-to-end with transactional source-document reuse/create, success-only `import_job` auditing, and canonical-record insert-or-skip behavior keyed by deterministic versioned fingerprints.
- Why: Complete the persistence boundary required before ledger modeling and analytics phases while preserving fail-fast behavior and rerun safety.
- Files: `app/pdf_persistence/{models.py,schemas.py,service.py,routes.py,tests/test_*.py}`, `alembic/versions/c8b0721b0977_add_pdf_persistence_schema.py`, `app/main.py`, `openspec/changes/add-postgres-persistence-for-canonical-pdf-records/tasks.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv uv run alembic upgrade head` (pass), `UV_CACHE_DIR=/tmp/uv uv run pytest -v app/pdf_persistence/tests` (13 passed), `UV_CACHE_DIR=/tmp/uv uv run pytest -v -m integration` (14 passed, 111 deselected), `UV_CACHE_DIR=/tmp/uv uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv uv run ty check app` (pass), `UV_CACHE_DIR=/tmp/uv uv run ruff check .` (pass), `UV_CACHE_DIR=/tmp/uv uv run black . --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` (no issues).
- Notes: Replay for this phase remains dependent on stored PDFs plus ingestion metadata manifests; v1 multi-source reconciliation remains deferred by design.

### docs(guides): update persistence reference guidance after 2.x-4.1 completion
- Summary: Updated baseline and extraction/golden-set guides to reflect implemented persistence behavior, including duplicate-safe reprocessing, success-only `import_job` rows, and replay/source-of-truth boundaries.
- Why: Remove stale guidance that still marked persistence as pending and make the implemented contract explicit for operators and AI agents.
- Files: `docs/guides/validation-baseline.md`, `docs/guides/pdf-extraction-guide.md`, `docs/guides/golden-set-contract.md`, `CHANGELOG.md`.
- Validation: `openspec validate --specs --all --json` confirms this change validates; existing unrelated spec-format failures remain in `spec/pdf-ingestion` and `spec/pdf-preflight-analysis` (missing required `## Purpose`/`## Requirements` sections).
- Notes: The pre-existing OpenSpec spec-validation issue remains unresolved and should be handled in a separate documentation/spec-format cleanup change.

### docs(commands): make commit-local force single all-in local commit
- Summary: Updated `.codex/commands/commit-local.md` to always stage full working tree (`git add -A`) and create one local commit, even when scope is mixed, while still stopping before any push.
- Why: Align command behavior with user expectation for an explicit all-in local packaging command.
- Files: `.codex/commands/commit-local.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: Reviewed command workflow and guardrails to confirm mixed scope no longer blocks commit-local execution.

### docs(commands): add local-only commit-local command
- Summary: Added `.codex/commands/commit-local.md` as a local-only companion to `/commit` that reviews staged, unstaged, and untracked work, stages the full intended tree, generates a descriptive commit message, creates the commit, and stops before any push.
- Why: Support the preferred workflow where commit creation can be automated locally while the final `git push` remains a separate manual user action.
- Files: `.codex/commands/commit-local.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: Reviewed command-index alignment and confirmed `commit-local` is listed in `.codex/commands/README.md`.

### docs(structure): reorganize repository documentation into product guides standards and references
- Summary: Reordered `docs/` into `product/`, `guides/`, `standards/`, and `references/`, moved all `*-standard.md` files into one shared `docs/standards/` directory, and added `docs/README.md` as the navigation index.
- Why: Reduce root-level clutter, make standards discoverable in one canonical location, and keep product, guide, and reference material clearly separated as the documentation set grows.
- Files: `docs/README.md`, `docs/product/*`, `docs/guides/*`, `docs/standards/*`, `docs/references/references.md`, `README.md`, `AGENTS.md`, `openspec/project.md`, `app/core/logging.py`, archived OpenSpec task notes, `CHANGELOG.md`.
- Validation: `rg -n "docs/(ruff-standard|black-standard|bandit-standard|mypy-standard|pyright-standard|pytest-standard|ty-standard|logging-standard|prd\.md|roadmap\.md|decisions\.md|references\.md|backlog-sprints\.md|reference-guides/)"` returned no remaining stale references.

### chore(validation): add Black and Bandit as first-class validation gates
- Summary: Added `ty` as an additional required type-check gate, raised Bandit gate thresholds to `high/high`, and propagated the updated baseline across governance/docs/command matrices.
- Why: Tighten security threshold policy and strengthen static typing coverage while keeping validation commands explicit and reproducible for both humans and AI agents.
- Files: `pyproject.toml`, `uv.lock`, `AGENTS.md`, `README.md`, `docs/standards/ty-standard.md`, `docs/standards/bandit-standard.md`, `docs/standards/black-standard.md`, `docs/guides/validation-baseline.md`, `docs/references/references.md`, `docs/product/backlog-sprints.md`, `.codex/commands/{README.md,plan.md,execute.md,validate.md}`, `openspec/changes/add-postgres-persistence-for-canonical-pdf-records/tasks.md`, `CHANGELOG.md`.
- Validation: `uv run ruff check .` (pass), `uv run black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (pass), `uv run ty check app` (pass), `uv run pytest -v -m "not integration"` (pass), `uv run pytest -v -m integration` (pass).

## 2026-03-19

### feat(pdf-ingestion): persist durable upload metadata manifests beside stored PDFs
- Summary: Updated PDF ingestion to write a JSON sidecar manifest for each stored upload and added a loader that recovers durable ingestion metadata from `storage_key` for later persistence work.
- Why: Lift the persistence-planning blocker where `storage_key` alone could not recover fields such as original filename, content type, file size, SHA-256, and page count after the initial upload response was gone.
- Files: `app/pdf_ingestion/service.py`, `app/pdf_ingestion/tests/test_service.py`, `app/pdf_ingestion/tests/test_routes.py`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/pdf_ingestion/tests` (12 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/pdf_ingestion` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/pdf_ingestion` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/pdf_ingestion` (0 errors).
- Notes: `uv run black ... --check` remained blocked in the sandbox because Black attempted to open a multiprocessing listener socket; formatting was not auto-verified through the Black gate in this session.

### feat(pdf-canonical): add dataset 1 canonical normalization and verification slices
- Summary: Implemented `pdf_normalization` and `pdf_verification` service/route slices to convert extracted dataset 1 rows into typed canonical records and produce deterministic mismatch reports against the checked-in golden contract.
- Why: Freeze trusted canonical contracts and verification evidence before starting PostgreSQL persistence and deduplication work.
- Files: `app/pdf_normalization/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/pdf_verification/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/main.py`, `openspec/changes/add-dataset-1-canonical-normalization-and-verification/tasks.md`.
- Validation: `uv run pytest -v app/pdf_normalization/tests app/pdf_verification/tests` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass), `uv run black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (no issues).
- Notes: Verification record pairing now uses deterministic fallback identity (`table_name` + `row_index` + `source_page`) so `splits` rows reconcile even when golden rows omit `row_id`.

### docs(reference-guides): record canonical baseline completion and persistence boundary
- Summary: Updated extraction and validation reference guides to reflect that extraction, normalization, and verification are implemented for dataset 1 while persistence remains pending.
- Why: Keep operational docs aligned with delivered behavior and avoid stale guidance that still marks canonical processing as unimplemented.
- Files: `docs/guides/pdf-extraction-guide.md`, `docs/guides/validation-baseline.md`.
- Validation: Documentation reviewed against current `app/pdf_extraction`, `app/pdf_normalization`, `app/pdf_verification` implementations and task checklist status.

## 2026-03-18

### chore(validation): integrate Black and Bandit as required baseline gates
- Summary: Added Black and Bandit as first-class validation layers in tooling/config and propagated the baseline command set across repo guidance and command docs.
- Why: Ensure formatting and security scanning are enforced consistently alongside Ruff, MyPy, Pyright, and pytest rather than remaining documentation-only guidance.
- Files: `pyproject.toml`, `uv.lock`, `.python-version`, `.codex/commands/{README.md,plan.md,execute.md,validate.md}`, `AGENTS.md`, `README.md`, `docs/guides/validation-baseline.md`, `docs/standards/ruff-standard.md`, `docs/standards/black-standard.md`, `docs/product/backlog-sprints.md`, `app/main.py`.
- Validation: `uv run ruff check .` (pass), `uv run --python 3.12.6 black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (pass), `uv run pytest -q` (100 passed).
- Notes: Added scoped `# nosec B104` on intentional dev bind in `app/main.py` to align Bandit with existing `# noqa: S104` policy.

### docs(quality-gates): add Black and Bandit standards for validation and security
- Summary: Added dedicated standards documentation for Black and Bandit, including configuration baselines, command usage, gate policy, and integration guidance with existing Ruff/MyPy/Pyright/Pytest workflow.
- Why: Formalize how to adopt Black and Bandit in a controlled way using official tooling guidance while keeping repository validation rules explicit and reproducible.
- Files: `docs/standards/black-standard.md`, `docs/standards/bandit-standard.md`, `docs/references/references.md`, `README.md`.
- Validation: Documentation-only update; content reviewed against official Black and Bandit docs and current repository validation structure.

### feat(pdf_extraction): add deterministic pdfplumber extraction from stored uploads
- Summary: Implemented `app/pdf_extraction` service and `/api/pdf/extract` route to parse dataset 1 tables from stored PDFs with deterministic row order, provenance, and explicit header/footer filtering.
- Why: Complete Sprint 1 Item 1.3 extraction slice before normalization/persistence work.
- Files: `app/pdf_extraction/service.py`, `app/pdf_extraction/routes.py`, `app/pdf_extraction/schemas.py`, `app/pdf_extraction/tests/test_service.py`, `app/pdf_extraction/tests/test_routes.py`, `app/main.py`, `pyproject.toml`, `docs/guides/pdf-extraction-guide.md`.
- Validation: `uv run pytest -v app/pdf_extraction/tests` (6 passed), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass).
- Notes: Current scope is raw extraction only; canonical mapping/normalization and persistence remain out of scope for this slice.

## 2026-03-17

### docs(commands): require explicit blast-radius and blind-spot diagnosis in /plan
- Summary: Tightened `/plan` so planning must explicitly diagnose blast radius and blind spots, and must state whether `CHANGELOG.md` updates are required.
- Why: Reduce hidden planning risk and make downstream contract propagation visible before implementation starts.
- Files: `.codex/commands/plan.md`, `.codex/commands/README.md`.
- Validation: Documentation review against current planning workflow and repo governance rules.

### docs(commands): overhaul OpenSpec command workflow and add /explain
- Summary: Reworked command docs for `/prime`, `/plan`, `/execute`; added `/explain`; synchronized command README.
- Why: Improve execution control, planning rigor, and repo-fit guidance for AI-assisted workflow.
- Files: `.codex/commands/prime.md`, `.codex/commands/plan.md`, `.codex/commands/execute.md`, `.codex/commands/explain.md`, `.codex/commands/README.md`.
- Validation: Documentation-only change; reviewed command coverage and examples.

## 2026-03-08

### docs: refine Codex command workflow guidance
- Summary: Updated command-layer documentation and workflow guidance.
- Why: Improve consistency and operator clarity.
- Files: Command docs and related guidance files.
- Validation: Documentation review.

### feat(pdf_ingestion): add PDF ingestion endpoint with preflight and local storage
- Summary: Added PDF ingestion flow with preflight validation and local storage behavior.
- Why: Enable end-to-end upload and preflight path for PDF workflows.
- Files: `app/pdf_ingestion/*`, routing/config/tests.
- Validation: Change tasks completed in OpenSpec; validation executed in implementation flow.

### feat(pdf_preflight): add PDF preflight analysis endpoint
- Summary: Introduced API support for PDF preflight analysis.
- Why: Provide validation and metadata extraction before downstream processing.
- Files: PDF preflight feature modules and tests.
- Validation: Feature validation executed during implementation cycle.

### feat(workflow): add Codex workflow commands and approval-gated commit flow
- Summary: Added repo-local command workflow for prime/plan/execute/validate/commit.
- Why: Standardize AI-assisted delivery process and approval checkpoints.
- Files: `.codex/commands/*`.
- Validation: Command documentation and flow checks.
