## 1. Fail-First Contract Coverage

- [ ] 1.1 Add fail-first backend tests for opportunity-scan request validation of explicit DCA controls (profile, threshold, multiplier).
- [ ] 1.2 Add fail-first backend tests proving `double_down_candidate` is blocked when 52-week eligibility is not evaluable.
- [ ] 1.3 Add fail-first frontend tests for operation-aware DCA control visibility in the composer.
- [ ] 1.4 Add fail-first frontend tests for recommendation-bubble catalog behavior (chat vs opportunity_scan, business-grade prompt scope).

## 2. Backend DCA Contract and Classification Wiring

- [ ] 2.1 Update copilot schema/service flow so opportunity scan uses request-provided DCA controls with strict validation semantics.
- [ ] 2.2 Preserve and harden deterministic action reason-code behavior for insufficient 52-week coverage and threshold evaluation boundaries.
- [ ] 2.3 Ensure opportunity response metadata remains compatible with typed response contracts after DCA control-path updates.

## 3. Frontend Copilot Control Surface and Payload Propagation

- [ ] 3.1 Add composer controls for DCA strategy profile, drawdown threshold, and multiplier under `opportunity_scan` mode.
- [ ] 3.2 Wire workspace session, API client normalization, and Zod schemas to submit selected DCA controls instead of hidden hardcoded defaults.
- [ ] 3.3 Polish recommendation-bubble copy and ordering so prompts stay portfolio/business informative and operation-aware.

## 4. Governance Closeout and Validation Evidence

- [ ] 4.1 Run backend validation gates for touched copilot modules (`pytest`, `mypy`, `pyright`, and related strict checks).
- [ ] 4.2 Run frontend validation gates for touched copilot surfaces (`lint`, `type-check`, `test`, `build`).
- [ ] 4.3 Update delivery docs (`CHANGELOG.md` and copilot guides) with DCA-control and recommendation-bubble contract changes.
- [ ] 4.4 Re-run OpenSpec status/validation checks and prepare implementation handoff notes.
