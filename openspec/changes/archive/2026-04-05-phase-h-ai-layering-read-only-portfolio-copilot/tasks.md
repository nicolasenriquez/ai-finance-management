## 1. Investigation and Contract Freeze

- [x] 1.1 Audit existing portfolio analytics service seams and freeze the v1 allowlisted tool set for copilot grounding.
  Notes:
  - Frozen allowlist/exclusion matrix is captured under `Contract Freeze (Task 1.x)` in `design.md`.
  - `get_portfolio_transactions_response` remains audited-but-excluded from model-visible context in v1 due to unbounded event-detail risk.
- [x] 1.2 Freeze the v1 copilot request/response contract, including concrete request bounds (max prior turns `8`, max user-input chars `2000`, max tool calls `6`), explicit response states (`ready`, `blocked`, `error`), evidence payload shape, and non-advice messaging.
  Notes:
  - Request/response fields and state-reason mappings are frozen in `design.md` (`Contract Freeze (Task 1.x)`).
  - Guardrail scenarios for bounded requests were added to `specs/portfolio-ai-copilot/spec.md`.
- [x] 1.3 Freeze the deterministic opportunity-scanner rule inputs, eligibility filters, ranking outputs, and insufficient-data rejection semantics.
  Notes:
  - Candidate selection remains rule-driven with frozen eligibility/ranking formula and deterministic tie-breakers.
  - Insufficient-data semantics now require explicit blocked state (`insufficient_context`) and no partial ranking.
- [x] 1.4 Freeze the Groq adapter contract for v1, including endpoint mode, model allowlist source, timeout/retry caps, and normalized reason-code mapping for provider failures.
  Notes:
  - Groq adapter endpoint/config/failure normalization are frozen in `design.md` and strengthened by scenarios in `specs/portfolio-ai-copilot/spec.md`.

## 2. Fail-First Test Baseline

- [x] 2.1 Add fail-first backend contract tests for the copilot chat endpoint request validation, typed success payload, and explicit blocked/error states.
  Notes:
  - Added `app/portfolio_ai_copilot/tests/test_chat_endpoint_contract_fail_first.py` with route registration, bounded-history validation, and typed `ready|blocked|error` contract assertions.
- [x] 2.2 Add fail-first backend safety tests proving raw canonical/private fields are excluded from model context and unsafe requests are rejected explicitly.
  Notes:
  - Added `app/portfolio_ai_copilot/tests/test_safety_boundaries_fail_first.py` covering exclusion-field contract, context sanitization behavior, and explicit boundary enforcement for execution/guarantee requests.
- [x] 2.3 Add fail-first backend tests for deterministic opportunity-scanner ranking and insufficient-input failures.
  Notes:
  - Added `app/portfolio_ai_copilot/tests/test_opportunity_scanner_fail_first.py` with deterministic replay expectation and typed insufficient-input rejection contract.
- [x] 2.4 Add fail-first frontend tests for copilot route rendering, loading/error/blocked/ready states, and evidence panel behavior.
  Notes:
  - Added `frontend/src/app/copilot-workspace.contract.fail-first.test.ts` to enforce `/portfolio/copilot` route and explicit UI state/evidence surfaces.
- [x] 2.5 Add fail-first frontend tests for opportunity-scan presentation, including separation of computed candidate data from AI narration.
  Notes:
  - Frontend contract test now asserts distinct opportunity candidate and narration markers before implementation.
- [x] 2.6 Add fail-first backend/frontend contract tests for normalized provider-failure mapping (`rate_limited`, `provider_blocked_policy`, `provider_misconfigured`, `provider_unavailable`) and corresponding UI state rendering.
  Notes:
  - Added backend mapping suite `app/portfolio_ai_copilot/tests/test_provider_reason_mapping_fail_first.py` and frontend reason-code mapping assertions in `frontend/src/app/copilot-workspace.contract.fail-first.test.ts`.

## 3. Backend AI Slice

- [x] 3.1 Create the backend `portfolio_ai_copilot` slice with typed schemas, route wiring, service orchestration, and tests.
  Notes:
  - Added `app/portfolio_ai_copilot/{schemas.py,service.py,routes.py,provider_groq.py}` and router wiring in `app/main.py`.
  - Backend contract/safety/opportunity/provider fail-first suite now passes against real module implementations.
- [x] 3.2 Add one fail-fast Groq provider adapter boundary using the frozen OpenAI-compatible chat-completions contract and required configuration (`GROQ_API_KEY`, model id, timeout, retry caps) without introducing fallback providers or persistent chat memory.
  Notes:
  - Missing provider configuration must fail explicitly rather than degrade silently.
  - Implemented fail-fast adapter config validation, allowlist enforcement, bounded retry behavior, and one OpenAI-compatible `/openai/v1/chat/completions` request path.
- [x] 3.3 Implement the allowlisted tool registry over approved portfolio analytics service seams and enforce privacy-minimized prompt assembly.
  Notes:
  - Added frozen allowlisted tool registry over approved `portfolio_analytics` service seams with bounded tool selection and max-call enforcement.
  - Added recursive `sanitize_model_context_payload` with frozen excluded-field markers for model-visible context minimization.
- [x] 3.4 Implement the copilot chat service and route with explicit evidence metadata, limitation messaging, and structured logging.
  Notes:
  - Added `/api/portfolio/copilot/chat` endpoint and typed request/response orchestration for `chat` + `opportunity_scan` operations.
  - Responses include explicit `state`, `reason_code`, evidence metadata, and limitation/non-advice messaging with structured lifecycle logs.
- [x] 3.5 Implement the deterministic opportunity-scanner service and expose it through the approved copilot contract.
  Notes:
  - Added deterministic candidate scoring (`0.45/0.35/0.20`) with frozen eligibility filters, stable tie-breaks, and explicit insufficient-context rejection.
  - Opportunity scan now returns deterministic candidate rows separately from AI narration in the same typed contract.
- [x] 3.6 Normalize provider/runtime failures into frozen reason codes and propagate typed blocked/error payloads for frontend state parity.
  Notes:
  - Added `map_provider_failure_to_copilot_state()` normalization to `rate_limited`, `provider_blocked_policy`, `provider_misconfigured`, and `provider_unavailable`.
  - Service now maps provider/runtime failures into typed `blocked|error` payloads with stable machine-readable reason codes.

## 4. Frontend Copilot Workspace

- [x] 4.1 Add the dedicated copilot workspace route/navigation entry and page shell within the portfolio frontend.
  Notes:
  - Added `/portfolio/copilot` route in `frontend/src/app/router.tsx` and a dedicated `PortfolioCopilotPage` module with workspace shell integration.
  - Added workspace navigation entry `Copilot (Read-only)` and updated navigation tests.
- [x] 4.2 Implement the chat interaction flow with explicit guardrails, bounded input handling, and deterministic state rendering.
  Notes:
  - Implemented bounded composer controls (message length, turn budgeting, scope/symbol readiness) and guarded submit flow.
  - Added explicit deterministic UI states (`idle`, `loading`, `blocked`, `error`, `ready`) with stable reason-code rendering.
- [x] 4.3 Implement grounded response rendering that separates answer text, evidence references, and limitation messaging.
  Notes:
  - Added typed frontend copilot schemas + API hook and wired response rendering for answer text, evidence list, and limitation list.
  - Added page tests covering ready/blocked/error state transitions and evidence/limitation surfaces.
- [x] 4.4 Implement opportunity-scan UI modules that show computed candidate signals separately from AI narration.
  Notes:
  - Added opportunity candidate table module and separate AI narration panel with deterministic candidate-first presentation.
  - Added dedicated test coverage for operation selector + opportunity candidate and narration rendering separation.
- [x] 4.5 Verify keyboard accessibility, responsive behavior, and alignment with existing workspace composition patterns.
  Notes:
  - Extended workspace keyboard-nav tests for copilot route and added responsive copilot styles for mobile layout behavior.
  - Verified full frontend gates (`lint`, full `test`, `build`) with updated workspace composition contracts.

## 5. Documentation and Governance

- [x] 5.1 Update product/docs artifacts that describe the AI layer scope, non-goals, and operator expectations.
  Notes:
  - At minimum, cover roadmap/backlog references, any affected API/UX guide content, and guardrail documentation for the copilot boundary.
  - Updated roadmap/backlog phase-10/sprint-9 status and expanded frontend API/UX guide coverage for copilot endpoint, route IA, contracts, and UX states.
- [x] 5.2 Add or update implementation-facing guidance for provider configuration, privacy posture, and validation expectations.
  Notes:
  - Added `docs/guides/portfolio-ai-copilot-guide.md` with fail-fast provider config contract, privacy minimization rules, reason-code semantics, and validation command baseline.
  - Updated `docs/guides/validation-baseline.md` with copilot implementation and verification expectations.
- [x] 5.3 Add `.env.example` placeholders and operator runbook guidance for Groq project-scoped keys, spend-limit posture, and model-permission controls.
  Notes:
  - Added copilot provider env placeholders in `.env.example` (`GROQ_API_KEY`, model, allowlist, timeout/retries, base URL).
  - Added explicit operator runbook guidance for project-scoped keys, spend limits, and model permission control in copilot guide.
- [x] 5.4 Add a `CHANGELOG.md` entry summarizing the delivered AI-layering slice and validation evidence.
  Notes:
  - Added `2026-04-04` changelog entry documenting backend/frontend AI-layer delivery scope and executed validation evidence.

## 6. Validation and Handoff

- [x] 6.1 Run backend quality gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) plus targeted backend AI and portfolio analytics tests.
  Notes:
  - Backend gates passed: `ruff`, `black --check --diff`, `mypy app/`, `pyright app/`, and `ty check app`.
  - Targeted backend suites passed: `app/portfolio_ai_copilot/tests` and `app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py` (with `ALLOW_INTEGRATION_DB_MUTATION=1`).
- [x] 6.2 Run frontend gates (`lint`, `test`, `build`) including the copilot workflow suites.
  Notes:
  - Frontend gates passed: `npm --prefix frontend run lint`, `npm --prefix frontend run test`, and `npm --prefix frontend run build`.
  - Copilot-specific suites passed, including `src/app/copilot-workspace.contract.fail-first.test.ts` and `src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx`.
- [x] 6.3 Run OpenSpec validation for the new change and all specs, then prepare the implementation handoff.
  Notes:
  - OpenSpec validation passed for change + full specs (`openspec validate phase-h-ai-layering-read-only-portfolio-copilot --type change --strict --json`, `openspec validate --specs --all --json`).
