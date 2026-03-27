## 1. Investigation and scope lock

- [x] 1.1 Confirm every current heavy market-refresh verification touchpoint before changing behavior.
Notes: Review `app/market_data/tests/test_service_integration.py`, `pyproject.toml`, `justfile`, `docs/guides/validation-baseline.md`, `docs/guides/yfinance-integration-guide.md`, and the product planning docs so the implementation updates the full verification contract rather than only one command or marker.
- [x] 1.2 Lock the intended lighter verification posture in tests before changing workflow wiring.
Notes: Start with failing or baseline-locking test updates for the representative non-core smoke lane, the retained `core` path, and the removal or retirement of routine `200` expectations so the contract is explicit before docs and command changes land.

## 2. Verification-lane implementation

- [x] 2.1 Update market-data integration markers and test organization so representative non-core smoke is the default broader-than-core lane.
Notes: Preserve current `core` integration coverage, keep representative non-core coverage deterministic, and avoid renaming existing `100` semantics to a smaller universe size.
- [x] 2.2 Remove or retire the routine `200` validation lane and reduce full `100` to explicit optional/manual coverage only.
Notes: This includes `pytest` markers, `just` command surfaces, and any helper text that still implies `200` or full `100` are routine local readiness gates.
- [x] 2.3 Keep refresh runtime semantics unchanged while rebalancing verification.
Notes: Do not add incremental backfill, watermark logic, snapshot-key changes, or broader currency fallback behavior in this change.

## 3. Documentation and planning alignment

- [x] 3.1 Update operator and validation docs to describe the lighter readiness contract.
Notes: Prioritize `docs/guides/validation-baseline.md`, `docs/guides/yfinance-integration-guide.md`, and any local workflow guidance tied to heavy market-refresh coverage.
- [x] 3.2 Update planning/history docs so Phase 6 status matches the rebalanced verification posture.
Notes: Align `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `README.md` if needed, and `CHANGELOG.md` so the repo no longer implies routine `100` or `200` readiness gates.

## 4. Verification

- [x] 4.1 Run targeted market-data tests that prove the new verification-lane contract.
Notes: Prefer the smallest set that proves the marker and smoke-lane behavior, such as targeted `pytest` nodes for market-data integration and CLI/workflow tests plus any updated marker selection checks.
- [x] 4.2 Run repository checks for the touched surfaces and record remaining limits explicitly.
Notes: Minimum expected commands are `openspec validate rebalance-market-refresh-verification-scope --type change --strict --json`, `openspec validate --specs --all --json`, `uv run pytest -v app/market_data/tests/test_service_integration.py app/data_sync/tests/test_data_sync_operations_cli.py`, and `git diff --check`; add `uv run ruff check` or targeted typing checks if implementation touches Python source outside tests/docs.
Notes: Validation executed with local constraints: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/tests/test_service_integration.py app/data_sync/tests/test_data_sync_operations_cli.py` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/data_sync/tests/test_data_sync_operations_cli.py` (7 passed), marker-aware collection for integration lanes (`integration and not market_scope_heavy`: 9/10 collected, `integration and market_scope_heavy`: 1/10 collected), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run alembic stamp base && PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m "integration and not market_scope_heavy"` (38 passed, 182 deselected), `OPENSPEC_TELEMETRY=0 openspec validate rebalance-market-refresh-verification-scope --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed), `git diff --check` (pass).
