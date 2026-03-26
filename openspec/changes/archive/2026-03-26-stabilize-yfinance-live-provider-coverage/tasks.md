## 1. Investigation and contract lock

Notes: Lock the narrower recovery contract before code changes so `empty history` and missing-currency handling do not drift into broad graceful degradation.
Notes: Evidence lock (2026-03-26): adapter treats `empty history` as terminal in `_download_symbol_history`, missing currency metadata as terminal in `_fetch_symbol_currency`, and refresh typed result currently exposes only `retry_attempted_symbols`/`failed_symbols` (no `history_fallback_*` or `currency_assumed_*` fields).

- [x] 1.1 Review current blocker evidence (`QQQM`, `AMD`, `XLF`) against adapter, refresh, and symbol-universe behavior to confirm the exact semantic recovery boundaries
- [x] 1.2 Add or update failing adapter tests for shorter-period fallback, fallback exhaustion, assumed default currency, and explicit invalid-currency rejection
- [x] 1.3 Add or update failing service tests for typed recovery evidence, `core` strictness, and `100/200` tolerance after bounded recovery

## 2. Provider and operations changes

Notes: Keep provider normalization concerns separate from orchestration policy and operator evidence.

- [x] 2.1 Extend typed settings and provider config for ordered history-period fallbacks, default currency, and bounded recovery controls
- [x] 2.2 Implement adapter recovery for empty-history fallback and assumed default currency while preserving fail-fast behavior for unsupported provider payloads
- [x] 2.3 Update refresh orchestration and typed result/schema surfaces (`app/market_data/schemas.py`, `app/data_sync/{schemas.py,service.py,tests/test_data_sync_operations_cli.py}`) to carry recovery diagnostics (`history_fallback_*`, `currency_assumed_*`) without relaxing required-symbol failure rules

## 3. Documentation and validation closeout

Notes: This change is operational and must close with both deterministic validation and explicit smoke evidence.
Notes: Smoke-evidence closeout (2026-03-26): deterministic blocker-evidence path captured via explicit exhaustion tests for adapter and `core` refresh required-symbol behavior.

- [x] 3.1 Update operational docs and product planning artifacts (`README.md`, `docs/guides/yfinance-integration-guide.md`, `docs/guides/validation-baseline.md`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `CHANGELOG.md`) to reflect the new recovery contract
- [x] 3.2 Run targeted validation for touched scope (`pytest`, `ruff`, `black --check`, `mypy`, `pyright`, and `ty` where applicable) and record evidence
- [x] 3.3 Run `openspec validate stabilize-yfinance-live-provider-coverage --type change --strict --json` and `openspec validate --specs --all --json`
- [x] 3.4 Run staged manual smoke (`core -> 100 -> 200`) or capture explicit blocker evidence after the new recovery contract is in place
