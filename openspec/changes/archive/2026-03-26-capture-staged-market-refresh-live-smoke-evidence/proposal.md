## Why

Phase 6 now has bounded `yfinance` recovery, staged refresh scopes, and explicit success/blocker evidence contracts, but the repository still lacks fresh live smoke evidence showing how the currently practical onboarding scopes (`core`, `100`) behave after the latest stabilization work. This proposal narrows the required smoke sequence to `core -> 100` so readiness is grounded in executable evidence rather than prolonged `200` runs.

## What Changes

- Capture fresh live smoke evidence for standalone `market-refresh-yfinance` runs across the staged onboarding sequence: `core`, then `100`.
- Capture one fresh `data-sync-local` smoke run after the staged refresh review to confirm current bootstrap-plus-refresh behavior under the same operator contract.
- Record the exact command invocations, prerequisites, timestamps, and resulting success/blocker evidence in dedicated repository documentation.
- Align market-data operator docs and product planning docs with the observed outcomes and current readiness posture after the new evidence is captured.
- Explicitly defer `200` smoke validation from this change and track it as future follow-up work under a separate proposal when runtime strategy and extraction scope are revisited.
- Keep implementation scope evidence-first: only propose follow-up code work if the fresh smoke runs uncover a new contract mismatch that is not already covered by the current stabilization changes.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `market-data-operations`: tighten the operator smoke requirement so fresh staged live evidence (`core -> 100`) and one follow-on combined sync run are captured and documented before current Phase 6 operator posture is treated as ready for downstream expansion.

## Impact

- OpenSpec change artifacts for the staged live smoke closeout.
- Market-data operator documentation and validation guidance.
- Product planning/readiness documentation (`roadmap`, `backlog`, `decisions`, `CHANGELOG`).
- Dedicated evidence artifact(s) under `docs/evidence/` for the refreshed live smoke results.
- Explicit follow-up note that `200` smoke validation is deferred from this change.
- Application code is expected to remain unchanged unless live evidence reveals a new mismatch that requires a separate follow-up change.
