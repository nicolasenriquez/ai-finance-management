## Why

The repository has a deterministic `yfinance` adapter, staged refresh scopes, and explicit operator evidence contracts, but the latest live smoke runs still fail on environment-dependent provider behavior for real symbols. Phase 6 is not complete until those blocker patterns are either absorbed safely into the approved runtime contract or rejected with clearer operational boundaries that let operators treat the refresh path as genuinely stable.

## What Changes

- Harden the live `yfinance` refresh path for the concrete blocker patterns already observed in staged smoke runs (`empty history` and missing currency metadata) without weakening fail-fast guarantees for unsupported or incomplete provider responses.
- Define how `core` versus `100/200` refresh scopes must behave when live-provider blockers affect only a subset of non-portfolio symbols, including which failures remain blocking and which outcomes may still persist safe rows.
- Tighten provider request pressure controls with conservative retry defaults and explicit per-symbol request pacing so staged onboarding runs reduce throttling exposure while preserving deterministic behavior.
- Tighten structured blocker and success evidence so operators can distinguish provider coverage gaps, metadata gaps, and recoverable partial-success outcomes across staged onboarding runs.
- Harden local dev/test database workflow safety so runtime commands and test commands cannot silently target the same database when operator validation is performed during this phase.
- Update tests and operator-facing documentation so Phase 6 closeout can be judged against one explicit contract for live-provider blocker handling.
- Keep current non-goals explicit: no market-enriched analytics expansion, no public market-data routes, no scheduler/queue infrastructure, and no ledger/canonical mutation in this change.

## Capabilities

### New Capabilities
- `dev-database-workflow-safety`: Add explicit runtime-vs-test database isolation guardrails in local `just` workflows so operational validation and test execution cannot silently mutate the same database.

### Modified Capabilities
- `market-data-provider-adapter`: Clarify the approved live-provider behaviors for empty-history and currency-metadata gaps, including which conditions must fail fast and which normalization/retry paths are allowed for safe continuation.
- `market-data-operations`: Update staged refresh-scope behavior and operator evidence so `core` remains strict for required portfolio coverage while `100/200` can report safe partial-success outcomes only under explicitly bounded conditions.
- `data-sync-operations`: Align local CLI/operator workflow expectations with the updated refresh blocker contract so `market-refresh-yfinance` and `data-sync-local` emit reproducible evidence for both blocked and safe-partial outcomes.

## Impact

- Affected code: `app/market_data/{providers/yfinance_adapter.py,service.py,schemas.py}`, `app/data_sync/service.py`, `scripts/data_sync_operations.py`, `justfile`, and related tests.
- Affected runtime behavior: staged live refresh runs may absorb a bounded subset of known provider failures for non-portfolio symbols while preserving strict fail-fast behavior for required coverage and unsupported payload semantics.
- Affected docs: `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{yfinance-integration-guide.md,validation-baseline.md,local-workflow-justfile.md}`, `README.md`, `.env.example`, and `CHANGELOG.md`.
- Follow-on leverage: this change is the operational closeout step needed before a later proposal can safely expand analytics contracts to market-enriched portfolio metrics.
