# Roadmap

## Phase 0: Product and Delivery Foundations

- Freeze PRD v1.
- Freeze canonical extraction contract for dataset 1.
- Establish baseline validation commands and expected outcomes.
- Align repository documentation with the finance MVP.

## Phase 1: PDF ETL Foundation

- Implement secure PDF ingestion.
- Add preflight checks for extractability.
- Implement primary extraction engine for multi-page tables.
- Normalize extracted rows into canonical JSON.
- Reconcile output against the golden set.

## Phase 2: Persistence Layer

- Add document metadata persistence.
- Add normalized transaction persistence in PostgreSQL.
- Define database models and migrations.
- Preserve provenance needed for audit and reprocessing.
- Add deterministic transaction fingerprints and duplicate-safe persistence behavior.
- Keep the current local PostgreSQL baseline with separated bootstrap and app credentials, while explicitly deferring stricter runtime-role hardening blocked by current software-version constraints.

## Phase 3: Ledger and Accounting Foundation

- Derive `portfolio_transaction`, `dividend_event`, `corporate_action_event`, `lot`, and `lot_disposition` from persisted canonical records.
- Freeze `dataset_1_v1` accounting policy: FIFO sell matching, trade USD basis fields, dividend income isolation, and proportional split lot adjustments.
- Keep fee/FX adjustments explicit as unsupported in v1 rather than inferred.
- Validate deterministic finance golden cases and duplicate-safe ledger rebuild behavior for reruns and concurrency.
- Keep market data storage and analytics API work out of this phase.

## Phase 4: Portfolio Analytics API

- Implemented `GET /api/portfolio/summary` grouped analytics from persisted ledger truth.
- Implemented `GET /api/portfolio/lots/{instrument_symbol}` with deterministic symbol normalization and explicit unknown-symbol rejection.
- Implemented ledger-only KPI v1 contract (`open_*`, `realized_*`, `dividend_*`) plus `as_of_ledger_at` consistency metadata.
- Added unit and DB-backed integration coverage proving analytics reads persisted ledger state and does not trigger rebuild/PDF pipeline side effects.
- Keep market-data-dependent valuation and unrealized pricing metrics deferred to later phases.

## Phase 5: Frontend Foundation And MVP Delivery

- Lock the frontend foundation before broad implementation:
  - design-system tokens for typography, color, spacing, motion, and responsive behavior
  - API-to-UI contract for summary, lot detail, formatting, and error handling
  - decimal-safe financial formatting rules and explicit unsupported-value boundaries
- Implement the frontend MVP against the current ledger-only analytics contract:
  - add React frontend container to Docker Compose
  - build grouped portfolio summary by instrument
  - build lot-detail drill-down from summary interactions
  - surface `as_of_ledger_at` and ledger-scope limitations clearly in the UI
- Harden the MVP before considering the phase complete:
  - validate explicit loading, empty, not-found, validation-failure, and server-failure states
  - meet WCAG 2.2 AA baseline expectations for focus, contrast, target size, and error identification
  - meet Core Web Vitals "good" thresholds for key screens and capture release evidence
  - keep market-value and FX-sensitive analytics deferred until market-data phases

## Phase 6: Market Data Boundary And External Broker Integration

- Implemented market-data ingestion boundary with dedicated `market_data_snapshot` and `price_history` persistence separated from canonical and ledger truth.
- Implemented fail-fast market-data write rules: explicit source provenance, deterministic symbol/time-key uniqueness, and `dataset_1`-anchored symbol support (including dotted tickers such as `BRK.B`).
- Implemented internal market-data read boundary for persisted symbol history without adding public market-data routes.
- Implemented market-enriched grouped summary (`GET /api/portfolio/summary`) with explicit pricing snapshot provenance and fail-fast open-position coverage checks.
- Kept lot-detail analytics (`GET /api/portfolio/lots/{instrument_symbol}`) ledger-only in this slice.
- Validated that market-data refresh remains idempotent and does not mutate canonical records, ledger events, lots, lot dispositions, dividends, or corporate actions.
- Implemented first external provider adapter (`yfinance`) for day-level close ingestion through `ingest_yfinance_daily_close_snapshot` and the existing market-data persistence contract.
- Froze first-slice provider semantics to deterministic day-level `Close` ingestion (`interval=1d`, `trading_date`, `auto_adjust=False`, `repair=False`) with bounded snapshot-key identity.
- Implemented one explicit full-refresh orchestration seam for the supported symbol universe via `refresh_yfinance_supported_universe`, keeping execution manual and schedule-ready in this slice.
- Implemented staged refresh-scope modes for the operator refresh seam: `core` (default), `100`, and `200`, with explicit fail-fast validation before provider ingest.
- Hardened provider payload-shape normalization to safely handle approved runtime `Close` shapes (series + tabular) and fail fast on unsupported payloads.
- Implemented local operator command workflows for deterministic `dataset_1` bootstrap and refresh execution:
  - `just data-bootstrap-dataset1`
  - `just market-refresh-yfinance`
  - `just data-sync-local`
  - equivalent module CLI: `uv run python -m scripts.data_sync_operations <command>`
- Extended operator command surfaces with optional refresh-scope propagation (`--refresh-scope core|100|200` in CLI and equivalent `just` positional override) to support controlled onboarding.
- Stabilized operator runbook/evidence posture for `market-refresh-yfinance` and `data-sync-local`: successful runs must emit typed refresh/sync evidence and blocked runs must emit structured fail-fast payloads (`status`, `stage`, `status_code`, `error`).
- Stabilized approved day-level temporal-key normalization for current live operations (`date`/`datetime`, `to_pydatetime()` returning `date`/`datetime`, scalar `item()` conversions) while preserving explicit fail-fast rejection for unsupported keys.
- Stabilized live-provider blocker patterns (2026-03-26): refresh now applies a bounded empty-history fallback ladder (`5y -> 3y -> 1y -> 6mo`) and explicit default-currency fallback (`USD`) for missing metadata, while keeping strict fail-fast behavior for unsupported payloads/invalid currency and required-symbol exhaustion.
- Current evidence snapshot (2026-03-26): refreshed smoke evidence captured for `core -> 100` plus one combined `data-sync-local --refresh-scope core` run (`docs/evidence/market-data/staged-live-smoke-2026-03-26.md`); `core` blocked (`502`, TSLA currency metadata access), `100` blocked (`408`, bounded timeout), combined sync completed.
- Current verification posture: `core` is the required live gate, representative non-core PR smoke is the default broader-than-core safeguard, full-scope `100` is optional manual soak coverage, and routine `200` validation is excluded from the local-first readiness workflow.
- Next in this phase: continue operational blocker resolution and refresh tuning from required `core` plus representative non-core evidence, while preserving non-goals (no ledger mutation, no public market-data router, no scheduler/queue infrastructure in this slice).

## Phase 7: Database Hardening and Deployment Readiness

- Revisit PostgreSQL and tooling version constraints that currently block stricter local and shared-environment hardening.
- Separate admin, migrator, and runtime roles more strictly once the software/runtime baseline allows it cleanly.
- Harden connection, privilege, and network posture for shared or hosted environments.
- Prepare TLS-ready PostgreSQL guidance for remote or hosted deployments.
- Re-validate extension and runtime compatibility before adopting advanced PostgreSQL features in stricter environments.

## Phase 8: Refactor and Code Health Checkpoint (Mandatory)

- Run a full technical-debt investigation across backend, frontend, tests, and documentation before opening new feature slices.
- Reduce high-complexity hotspots and oversized modules while preserving existing behavior contracts.
- Reconcile backend/frontend schema and route contracts to remove drift introduced by active delivery phases.
- Enforce repository quality gates as release-blocking:
  - backend: `ruff`, `black --check`, `mypy`, `pyright`, `ty`, unit tests, and integration tests
  - frontend: `lint`, `type-check`, `test`, and `build`
- Close governance debt in source-of-truth docs and OpenSpec artifacts so phase status and capability specs remain synchronized.
- Refresh security and frontend evidence posture after refactor closeout (`bandit`, accessibility, keyboard walkthroughs, CWV evidence).
- Keep this phase non-feature by default: no net-new product capability is required for completion.

## Phase 9: QuantStats Monte Carlo and Risk Evolution

- Extend portfolio analytics contracts with risk-evolution datasets:
  - drawdown path timeline
  - rolling volatility timeline
  - rolling beta timeline
  - deterministic return-distribution buckets
- Add bounded Monte Carlo diagnostics for both `portfolio` and `instrument_symbol` scopes with explicit assumptions and seeded determinism.
- Add default-on profile scenario comparison (`Conservative`, `Balanced`, `Growth`) with one-run deterministic comparability and historical calibration basis controls (`monthly`, `annual`, `manual`).
- Extend Quant report generation metadata with explicit simulation-context lifecycle (`ready`, `unavailable`, `error`) and omission reasons.
- Keep scope semantics symmetric across analytics, risk, simulation, and report workflows (`portfolio` vs `instrument_symbol`).
- Keep portfolio P&L semantics explicit by route:
  - Home: executive realized/unrealized/period P&L snapshot
  - Analytics: contribution decomposition and concentration context
  - Quant/Reports: scenario-forward probability diagnostics
- Add frontend dense-table and control-surface polish for professional readability:
  - semantic Quant lens table (`30D`/`90D`/`252D`) with aligned numeric columns
  - compact Quant report lifecycle control cluster
  - contribution table label hardening (`signed`, `net share`, `absolute share`)
  - hierarchy default sector-collapsed load with sortable header affordances

Explicit non-goals for this phase:

- no portfolio optimization or allocation recommendation engine
- no trade execution workflows
- no financial-advice or predictive-certainty claims from Monte Carlo output
- no scheduler/queue infrastructure expansion

## Phase 10: AI Layering v1 - Read-Only Portfolio Copilot (Post-MVP Extension)

- Add a read-only portfolio copilot that answers questions over approved aggregated analytics context rather than direct database access.
- Freeze an AI safety envelope for v1:
  - allowlisted read-only tools only
  - no raw canonical PDF payload access
  - no direct SQL or unrestricted "ask the database" workflows
  - no trade execution, rebalancing automation, or guaranteed-return claims
- Add deterministic opportunity-scanner workflows for candidate additions or "discount" ideas, with explicit rule-driven ranking and AI narration layered on top.
- Add a dedicated frontend copilot workspace surface with evidence-backed responses, visible limitations, and explicit non-advice messaging.
- Keep the first AI slice stateless and minimal:
  - no vector store or document RAG
  - no persistent chat memory
  - no multi-agent orchestration

Explicit non-goals for this phase:

- no direct access from the model to raw canonical persistence tables
- no autonomous trade execution or broker-side actions
- no opaque model-only stock-picking logic without deterministic scoring evidence
- no template-wide AI platform migration, auth expansion, or RAG/vector infrastructure
- no financial-advice claims presented as certainty

## Deferred Phases

- authentication and authorization
- broader agentic automation, persistent memory, and RAG beyond the read-only copilot
- Supabase migration
- production cloud deployment
