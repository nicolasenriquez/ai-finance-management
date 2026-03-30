## 1. Investigation and Contract Freeze

- [ ] 1.1 Audit existing portfolio analytics service seams and freeze the v1 allowlisted tool set for copilot grounding.
  Notes:
  - Confirm which existing summary, time-series, contribution, risk, hierarchy, transaction, and Monte Carlo reads are safe to expose as model-visible aggregated context.
  - Record excluded sources explicitly, especially raw canonical payloads and any unbounded transaction detail.
- [ ] 1.2 Freeze the v1 copilot request/response contract, including bounded history limits, explicit response states, evidence payload shape, and non-advice messaging.
- [ ] 1.3 Freeze the deterministic opportunity-scanner rule inputs, eligibility filters, ranking outputs, and insufficient-data rejection semantics.
  Notes:
  - Candidate selection must remain rule-driven; AI is narration only.

## 2. Fail-First Test Baseline

- [ ] 2.1 Add fail-first backend contract tests for the copilot chat endpoint request validation, typed success payload, and explicit blocked/error states.
- [ ] 2.2 Add fail-first backend safety tests proving raw canonical/private fields are excluded from model context and unsafe requests are rejected explicitly.
- [ ] 2.3 Add fail-first backend tests for deterministic opportunity-scanner ranking and insufficient-input failures.
- [ ] 2.4 Add fail-first frontend tests for copilot route rendering, loading/error/blocked/ready states, and evidence panel behavior.
- [ ] 2.5 Add fail-first frontend tests for opportunity-scan presentation, including separation of computed candidate data from AI narration.

## 3. Backend AI Slice

- [ ] 3.1 Create the backend `portfolio_ai_copilot` slice with typed schemas, route wiring, service orchestration, and tests.
- [ ] 3.2 Add one fail-fast provider adapter boundary and required configuration for the approved model provider without introducing fallback providers or persistent chat memory.
  Notes:
  - Missing provider configuration must fail explicitly rather than degrade silently.
- [ ] 3.3 Implement the allowlisted tool registry over approved portfolio analytics service seams and enforce privacy-minimized prompt assembly.
- [ ] 3.4 Implement the copilot chat service and route with explicit evidence metadata, limitation messaging, and structured logging.
- [ ] 3.5 Implement the deterministic opportunity-scanner service and expose it through the approved copilot contract.

## 4. Frontend Copilot Workspace

- [ ] 4.1 Add the dedicated copilot workspace route/navigation entry and page shell within the portfolio frontend.
- [ ] 4.2 Implement the chat interaction flow with explicit guardrails, bounded input handling, and deterministic state rendering.
- [ ] 4.3 Implement grounded response rendering that separates answer text, evidence references, and limitation messaging.
- [ ] 4.4 Implement opportunity-scan UI modules that show computed candidate signals separately from AI narration.
- [ ] 4.5 Verify keyboard accessibility, responsive behavior, and alignment with existing workspace composition patterns.

## 5. Documentation and Governance

- [ ] 5.1 Update product/docs artifacts that describe the AI layer scope, non-goals, and operator expectations.
  Notes:
  - At minimum, cover roadmap/backlog references, any affected API/UX guide content, and guardrail documentation for the copilot boundary.
- [ ] 5.2 Add or update implementation-facing guidance for provider configuration, privacy posture, and validation expectations.
- [ ] 5.3 Add a `CHANGELOG.md` entry summarizing the delivered AI-layering slice and validation evidence.

## 6. Validation and Handoff

- [ ] 6.1 Run backend quality gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) plus targeted backend AI and portfolio analytics tests.
- [ ] 6.2 Run frontend gates (`lint`, `test`, `build`) including the copilot workflow suites.
- [ ] 6.3 Run OpenSpec validation for the new change and all specs, then prepare the implementation handoff.
