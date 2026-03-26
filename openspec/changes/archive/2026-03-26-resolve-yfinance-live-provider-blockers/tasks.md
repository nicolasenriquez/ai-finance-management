## 1. Investigation and contract lock

Notes: Confirm live blocker classes and operational failure boundaries before widening implementation.

- [x] 1.1 Review current live blocker evidence (`QQQM`, `AMD`, `XLF`) against adapter, refresh, and CLI behavior to lock approved blocker categories and required-portfolio boundaries
- [x] 1.2 Add or update unit tests that pin provider retry/pacing behavior and adapter fail-fast classification boundaries
- [x] 1.3 Add or update service tests that pin `core` strictness, `100/200` bounded tolerance behavior, and structured refresh evidence fields

## 2. Provider and operations implementation

Notes: Keep provider normalization concerns separate from scope-policy and operator evidence concerns.

- [x] 2.1 Add conservative rate-control defaults (`max_retries=1`) and configurable per-symbol request spacing in typed settings/config path
- [x] 2.2 Wire request pacing through yfinance adapter fetch loop and staged per-symbol scope fetch loops while preserving strict required-symbol failure handling
- [x] 2.3 Reconcile remaining data-sync/CLI contract impacts and confirm no additional command payload/schema updates are required for this branch

## 3. Local workflow database safety alignment

Notes: This slice is included in current branch scope and must be represented explicitly in OpenSpec to keep implementation and proposal consistent.

- [x] 3.1 Add runtime/test DB isolation guardrails in `just` workflows (`db-runtime-guard`, `test-db-check`, `test-db-upgrade`) and apply them to `dev`, `test`, and `test-integration` flows
- [x] 3.2 Update `.env.example` and `README.md` to require explicit `TEST_DATABASE_URL` separation from runtime `DATABASE_URL`
- [x] 3.3 Update `docs/guides/local-workflow-justfile.md` and `docs/guides/validation-baseline.md` so documented commands match guarded runtime/test database behavior

## 4. Documentation and validation closeout

Notes: Phase 6 closeout requires both deterministic checks and explicit operational evidence.

- [x] 4.1 Update `CHANGELOG.md` with implementation summary, rationale, touched files, and validation evidence
- [x] 4.2 Run targeted validation for touched scope (`pytest`, `ruff`, `black --check`, `mypy`, `pyright`) and capture outcomes
- [x] 4.3 Run `openspec validate --specs --all` and confirm change/spec contract validity
- [x] 4.4 Run staged manual smoke (`core -> 100 -> 200`) or record explicit blocker payload evidence, then finalize task completion state

## Execution Notes

Notes: Evidence captured on March 25, 2026 in local branch `feat/yfinance-live-blockers-20260325`.

- Validation evidence: targeted `pytest` for touched market-data/core tests passed; `ruff check`, `black --check --diff`, `mypy`, and `pyright` passed for touched scope.
- OpenSpec evidence: `openspec validate resolve-yfinance-live-provider-blockers --type change --strict --json` passed.
- OpenSpec global evidence: `openspec validate --specs --all --json` passed (`15/15` items valid).
- Manual smoke evidence (`market-refresh-yfinance`):
- `--refresh-scope core` failed with explicit `502` payload (`YFinance did not provide currency metadata for symbol 'AMD'.`), confirming strict required-symbol fail-fast behavior.
- `--refresh-scope 100` failed with explicit `502` payload after retry (`YFinance retry could not recover required portfolio symbol(s)`), confirming required-portfolio gating is preserved.
- `--refresh-scope 200` failed with explicit `502` payload after retry on the same required symbol set, confirming staged scope behavior and blocker evidence consistency.
