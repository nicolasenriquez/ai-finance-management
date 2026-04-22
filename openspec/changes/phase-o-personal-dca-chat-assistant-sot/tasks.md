## 0. Dependency Gates

- [ ] 0.1 Confirm `phase-k-dca-controls-and-governance-closeout` is implemented and validated.
- [ ] 0.2 Confirm `archive-v0-and-build-compact-trading-dashboard` has stable copilot container/shell integration points for assistant embedding.

## 1. Fail-First Contract Coverage

- [ ] 1.1 Add fail-first backend schema tests for `dca_assessment` operation request/response payloads.
- [ ] 1.2 Add fail-first backend tests for typed personal-policy-context validation and insufficiency semantics.
- [ ] 1.3 Add fail-first backend tests for deterministic DCA calculator outputs and bounded numeric ranges.
- [ ] 1.4 Add fail-first backend tests for context-card synthesis contract (gainers/losers/news summary) with explicit insufficiency behavior.
- [ ] 1.5 Add fail-first backend tests for event-stream and session-persistence contract bounds.
- [ ] 1.6 Add fail-first frontend tests for mode-specific composer behavior (`chat`, `opportunity_scan`, `dca_assessment`).
- [ ] 1.7 Add fail-first frontend tests for event-aware lifecycle and tool-call timeline rendering.
- [ ] 1.8 Add fail-first frontend tests for persisted-session replay and evidence continuity.

## 2. Backend DCA SOT Engine and Tooling

- [ ] 2.1 Extend copilot operation enums/contracts to include `dca_assessment` with strict typing.
- [ ] 2.2 Implement deterministic DCA SOT policy evaluation pipeline for personal assessments.
- [ ] 2.3 Implement DCA calculator toolpack (scenario comparison, cost-basis projection, concentration delta, threshold monitor).
- [ ] 2.4 Ensure narration is grounded in deterministic outputs and preserves proxy/non-advice caveats.
- [ ] 2.5 Implement deterministic context-card synthesis (gainers/losers/news summary) with evidence metadata.
- [ ] 2.6 Implement event-stream payload semantics for request lifecycle and tool-call traces.
- [ ] 2.7 Implement bounded conversation persistence and evidence-linked replay semantics.
- [ ] 2.8 Keep bounded read-only tool orchestration and reason-code stability for blocked/error states.

## 3. Frontend Personal Assistant Workspace

- [ ] 3.1 Add `dca_assessment` mode controls and typed policy-context input affordances in copilot composer.
- [ ] 3.2 Add calculator output surfaces with clear deterministic/evidence labeling.
- [ ] 3.3 Add context-card modules (gainers/losers/news summary) with explicit unavailable state rendering.
- [ ] 3.4 Add event-aware response timeline for lifecycle and tool-call transparency.
- [ ] 3.5 Add session replay and continuity UX for persisted DCA assistant threads.
- [ ] 3.6 Preserve continuity across docked panel, expanded route, and mobile full-screen surfaces.
- [ ] 3.7 Ensure recommendation chips map to DCA SOT categories and remain non-executing.

## 4. Governance, Validation, and Handoff

- [ ] 4.1 Run backend validation gates for touched copilot modules (`pytest`, `mypy`, `pyright`, strict checks).
- [ ] 4.2 Run frontend validation gates for touched copilot surfaces (`lint`, `type-check`, `test`, `build`).
- [ ] 4.3 Add observability instrumentation docs and validation evidence for lifecycle/tool/token/error telemetry.
- [ ] 4.4 Update copilot and product docs with DCA SOT policy semantics, calculator definitions, and context-card contracts.
- [ ] 4.5 Update `CHANGELOG.md` with delivered behavior and validation evidence.
- [ ] 4.6 Re-run OpenSpec status/validation checks and capture implementation handoff notes.
