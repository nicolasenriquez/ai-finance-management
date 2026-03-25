## Why

The repository now has manual `yfinance` refresh and combined data-sync operator commands, but the operational path is not yet stable enough to treat as implementation-ready for later market-enriched analytics. The latest delivery evidence recorded a real live-provider smoke blocker, and Phase 6 explicitly calls for runbook/scheduling stabilization before analytics contract expansion.

## What Changes

- Stabilize the current market-data operator workflow by defining one approved live-smoke/runbook path for `market-refresh-yfinance` and `data-sync-local`, including how success, failure, and blocker evidence must be captured.
- Harden the current `yfinance` operational path for approved live runtime response variations that should be accepted without weakening existing fail-fast behavior for truly unsafe payloads.
- Formalize a schedule-ready invocation posture on top of the existing local command surfaces without introducing scheduler or queue infrastructure in this slice.
- Update validation and operator documentation so market-data refresh closeout requires explicit smoke evidence and a documented blocker path when provider/network/runtime conditions prevent safe completion.
- Keep current non-goals explicit: no public market-data router, no ledger/canonical mutation, no broker-authenticated provider expansion, and no market-enriched analytics/API/frontend expansion in this change.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `market-data-operations`: Extend the operational contract so the approved refresh workflows include explicit runbook steps, smoke-evidence expectations, schedule-ready invocation guidance, and blocker recording rules for environment-dependent failures.
- `market-data-provider-adapter`: Clarify which live `yfinance` response-shape or date-key variants are accepted for the current operational refresh path, while preserving fail-fast rejection for unsupported or incomplete payloads.

## Impact

- Affected code: `app/market_data/`, `app/data_sync/`, `scripts/data_sync_operations.py`, and touched tests around operational refresh behavior.
- Affected runtime behavior: live operator refresh/sync runs gain a more explicit operational contract and may accept additional approved runtime payload variations needed for stable smoke execution.
- Affected systems: local operator workflows, market-data refresh validation, and future scheduler integration posture.
- Affected docs: `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md,local-workflow-justfile.md}`, `docs/standards/market-data-provider-standard.md`, and `CHANGELOG.md`.
- Follow-on leverage: this change is the last Phase 6 hardening slice before market-enriched analytics proposals can rely on the market-data refresh workflow as a trustworthy input.
