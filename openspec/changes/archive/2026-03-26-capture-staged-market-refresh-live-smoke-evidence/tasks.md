## 1. Investigation and evidence setup

- [x] 1.1 Review current market-data operator docs, validation guidance, and archived blocker evidence to confirm the required staged commands, evidence fields, and readiness target.
Notes: Confirm the current Phase 6 operator contract before running any live command so the evidence artifact reflects the promised scope, fields, and readiness target rather than ad hoc interpretation.
Notes: Updated staged commands for this change to standalone refresh sequence (`core -> 100`) plus one follow-on `data-sync-local` run.
Notes: Confirmed required evidence fields from `docs/guides/validation-baseline.md`, `docs/guides/yfinance-integration-guide.md`, and archived market-data changes: typed success payload fields plus blocker payload fields (`status`, `stage`, `status_code`, `error`).
- [x] 1.2 Create the dedicated market-data evidence artifact location and capture template for command, timestamp, prerequisites, success fields, and blocker fields.
Notes: Keep the evidence template explicit enough to capture either typed success payloads or structured blocker payloads without re-parsing logs later.
Notes: Created dedicated evidence location and template at `docs/evidence/market-data/staged-live-smoke-template.md` with environment snapshot, staged command log, and explicit success/blocker extraction sections.

## 2. Fresh live smoke capture

- [x] 2.1 Run fresh standalone `market-refresh-yfinance` smoke for `core` and `100`, recording typed success evidence or structured blocker evidence for each stage.
Notes: Run the staged sequence in order (`core -> 100`) so later outcomes are interpreted in the context of narrower-scope behavior.
Notes: This change may close with blocker evidence if the environment or provider still prevents safe completion; do not reinterpret blocked runs as success.
Notes: This change explicitly defers `200` smoke evidence and should document that deferral clearly in readiness artifacts.
Notes: Captured blocker evidence for both standalone stages in `docs/evidence/market-data/staged-live-smoke-2026-03-26.md` (`core` failed with TSLA metadata access `502`; `100` exceeded bounded 360s runtime and was recorded as explicit timeout blocker `408`).
- [x] 2.2 Run one fresh `data-sync-local` smoke invocation after the staged refresh review and record the combined bootstrap-plus-refresh outcome honestly.
Notes: Use the current combined operator contract as-is and capture whether the refresh stage behavior matches the standalone staged evidence.
Notes: Captured one successful combined run in `docs/evidence/market-data/staged-live-smoke-2026-03-26.md` (`status=completed`, nested `market_refresh.status=completed`, `refresh_scope_mode=core`).
- [x] 2.3 If a live run exposes a new contract mismatch that is not already covered by current docs, stop and document the blocker clearly before proposing any follow-up implementation work.
Notes: Do not widen this change into new app code unless the fresh smoke proves the documented operator contract and current implementation no longer match.
Notes: Treat deferred `200` smoke validation as explicit follow-up scope, not as implied readiness.
Notes: No new app-code contract mismatch was introduced in this run; blockers are operational evidence (provider metadata failure for required symbol and bounded-time runtime exhaustion) and are documented for planning/readiness updates.

## 3. Documentation and readiness alignment

- [x] 3.1 Update operator and validation docs to link the fresh evidence artifact and reflect the observed current readiness posture.
Notes: Prioritize `docs/guides/validation-baseline.md`, `docs/guides/yfinance-integration-guide.md`, and related operator workflow guidance.
Notes: Updated operator guidance to link `docs/evidence/market-data/staged-live-smoke-2026-03-26.md`, align manual smoke scope to `core -> 100`, and preserve explicit deferred-scope recording for `200`.
- [x] 3.2 Update product planning/history docs (`roadmap`, `backlog`, `decisions`, `CHANGELOG`) so the remaining Phase 6 status matches the fresh live evidence.
Notes: Keep the repository history honest about whether the refreshed runs succeeded, remained blocked, or revealed a narrower operational posture than previously implied.
Notes: State clearly that this change validates `core` and `100` only, and that `200` is deferred follow-up scope.
Notes: Updated `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}` plus `CHANGELOG.md` with the captured evidence posture (`core` blocker `502`, `100` blocker `408`, combined `data-sync-local` with `core` completed) and explicit `200` deferral.
- [x] 3.3 Validate that the OpenSpec proposal/spec/design/tasks stay aligned with the final documented operator posture.
Notes: Keep app code unchanged unless Task 2.3 proves that a separate implementation change is necessary.
Notes: Alignment here includes keeping this change contract at `core -> 100` and preserving explicit `200` deferral messaging.
Notes: OpenSpec proposal/design/spec/task artifacts remain aligned with the final documented posture after evidence capture and doc updates.

## 4. Verification

- [x] 4.1 Run `openspec validate capture-staged-market-refresh-live-smoke-evidence --type change --strict --json`.
Notes: This confirms the change artifact set remains structurally valid after documentation and evidence updates.
- [x] 4.2 Run `openspec validate --specs --all --json` and `git diff --check`, then record any remaining non-blocking environment noise separately from validation results.
Notes: Prefer the smallest verification set that proves the artifact set is internally consistent; only add code validation if execution changes code or command behavior.
Notes: Verification results were clean (`openspec validate --specs --all --json`: 16/16 passed; `git diff --check`: pass). No non-blocking environment noise observed in this run.
