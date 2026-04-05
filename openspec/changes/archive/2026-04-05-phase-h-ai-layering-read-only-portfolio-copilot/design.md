## Context

The repository now has the core technical shape needed for a narrow AI layer: persisted canonical records, derived ledger truth, market-data separation, typed analytics contracts, and a multi-route frontend workspace. The highest-leverage next step is not broad agentic automation, but a read-only copilot that can explain portfolio state and narrate deterministic research outputs without weakening privacy or trust boundaries.

Current-state audit:

- `app/portfolio_analytics/routes.py` already exposes rich read-only analytics surfaces for summary, time series, contribution, risk, Monte Carlo, hierarchy, and transactions.
- `app/pdf_persistence/models.py` still contains raw canonical payloads and provenance detail that should remain outside v1 model-visible context.
- `frontend/src/app/router.tsx` already supports dedicated analytical surfaces, so adding a focused copilot route does not require a UI architecture reset.
- `docs/references/full-stack-ai-agent-template-evaluation.md` already recommends selective pattern borrowing from the external AI template and rejects broad drop-in adoption.

This design keeps the repository aligned with KISS, YAGNI, strict typing, and fail-fast behavior while activating a narrow AI boundary that is useful now.

## Goals / Non-Goals

**Goals:**
- Add a minimal backend AI slice for grounded portfolio chat over approved read-only portfolio tools.
- Add a deterministic opportunity scanner whose selection logic is inspectable and testable.
- Add a dedicated frontend copilot experience with explicit evidence, limits, and non-advice messaging.
- Preserve privacy by excluding raw canonical payloads and direct database access from model context.
- Freeze one explicit Groq provider contract (endpoint mode, model allowlist, timeout/retry, and error mapping) before coding.
- Keep the change implementation-local, test-first, and compatible with current validation gates.

**Non-Goals:**
- Full migration to the external AI template or any multi-framework agent stack.
- Vector search, RAG ingestion, persistent conversation memory, or multi-agent orchestration.
- Trade execution, portfolio rebalancing automation, or guaranteed-return recommendations.
- Multi-provider abstraction in v1 (this slice remains Groq-only behind one adapter boundary).
- Rewriting existing analytics contracts unless a later implementation task proves a concrete gap.

## Decisions

### Decision 1: Build one new vertical slice for AI instead of spreading AI logic across existing modules
- Decision: Introduce a dedicated backend slice such as `app/portfolio_ai_copilot/` for routes, schemas, service orchestration, provider adapter, and tests.
- Rationale: keeps AI concerns localized, typed, and easy to disable without contaminating ledger or analytics modules.
- Alternatives considered:
  - fold AI orchestration into `app/portfolio_analytics/`: rejected because it would mix deterministic analytics with model orchestration concerns.
  - adopt the external template structure wholesale: rejected because the current repo does not need auth, RAG, or multi-framework runtime complexity.

### Decision 2: Ground tool execution in approved analytics application services, not internal HTTP calls or SQL
- Decision: Copilot tools will call approved portfolio application/service seams directly while preserving the same validation and scope semantics as existing portfolio routes.
- Rationale: avoids HTTP-in-HTTP overhead and avoids bypassing domain validation through ad hoc SQL.
- Alternatives considered:
  - direct database querying tools: rejected because they weaken privacy and trust boundaries.
  - internal HTTP calls to local endpoints: rejected because they duplicate serialization and error handling without adding safety.

### Decision 3: Keep v1 chat stateless, bounded, and request/response based
- Decision: Use a typed HTTP request/response contract with bounded conversation history and no required server-side conversation persistence in v1, with concrete limits:
  - max prior turns: `8`
  - max user message length: `2000` characters
  - max tool invocations per request: `6`
- Rationale: minimizes privacy risk, reduces infrastructure requirements, and keeps fail-fast behavior obvious.
- Alternatives considered:
  - WebSocket streaming first: rejected as unnecessary for the first useful slice.
  - persistent chat threads: rejected until the product proves a need for stored conversation history.

### Decision 4: Freeze a strict tool and context safety envelope
- Decision: The copilot will use an allowlisted tool registry over aggregated analytics outputs only, with prompt assembly that excludes raw canonical payloads, direct DB access, and hidden fallback behavior.
- Rationale: the repository already separates truth boundaries well; the AI layer should preserve them instead of bypassing them.
- Alternatives considered:
  - unrestricted "ask the database" chatbot: rejected because it increases privacy exposure and makes output quality difficult to validate.
  - raw document/RAG context in v1: rejected because the first user value is portfolio understanding, not statement-document search.

### Decision 5: Make opportunity discovery deterministic first and narrative second
- Decision: Opportunity scanning will use explicit scoring rules or filters for candidate generation, while the model explains the computed results and caveats.
- Rationale: keeps candidate selection testable and reduces the chance of opaque or inconsistent recommendations.
- Alternatives considered:
  - fully model-driven stock selection: rejected because it is harder to validate and easier to misinterpret as financial advice.

### Decision 6: Add a dedicated `Copilot` workspace surface with evidence-first rendering
- Decision: The frontend will expose a dedicated copilot route or equivalent stable workspace surface, likely `/portfolio/copilot`, with separated answer, evidence, and opportunity-result sections.
- Rationale: avoids overloading Home, Risk, or Quant/Reports and keeps the AI boundary explicit to the user.
- Alternatives considered:
  - embedding chat into Home: rejected because it dilutes the executive-summary role of Home.
  - hiding the workflow inside Quant/Reports: rejected because chat and opportunity explanation are broader than report generation.

### Decision 7: Freeze Groq integration on one OpenAI-compatible chat-completions adapter
- Decision: Implement one provider adapter that targets Groq's OpenAI-compatible chat-completions API boundary with one configured model allowlist and no fallback provider.
- Rationale: keeps provider behavior explicit, avoids accidental multi-provider complexity, and aligns with KISS/YAGNI.
- Alternatives considered:
  - Groq + fallback provider chain: rejected because silent fallback conflicts with fail-fast policy.
  - provider-agnostic orchestration layer in v1: rejected as unnecessary abstraction before product fit is proven.

### Decision 8: Map provider/runtime failures to stable blocked/error reason codes
- Decision: Normalize provider failures into stable response reasons for UI parity:
  - `rate_limited` (provider 429)
  - `provider_blocked_policy` (provider 403 policy, spend, or model-permission block)
  - `provider_misconfigured` (missing/invalid key, invalid model id, invalid adapter config)
  - `provider_unavailable` (timeouts, 5xx, transient upstream failures)
- Rationale: supports explicit `blocked`/`error` UX states and avoids ambiguous generic failures.
- Alternatives considered:
  - pass-through raw provider messages directly to UI: rejected because it is unstable and can leak provider-specific detail.

## Contract Freeze (Task 1.x)

### 1.1 Allowlisted grounding tools and explicit exclusions

Approved v1 grounding tool IDs (backed by existing read-only service seams):

- `portfolio_summary` -> `get_portfolio_summary_response`
- `portfolio_time_series` -> `get_portfolio_time_series_response`
- `portfolio_contribution` -> `get_portfolio_contribution_response`
- `portfolio_risk_estimators` -> `get_portfolio_risk_estimators_response`
- `portfolio_risk_evolution` -> `get_portfolio_risk_evolution_response`
- `portfolio_return_distribution` -> `get_portfolio_return_distribution_response`
- `portfolio_hierarchy` -> `get_portfolio_hierarchy_response`
- `portfolio_monte_carlo` -> `generate_portfolio_monte_carlo_response`
- `portfolio_health_synthesis` -> `get_portfolio_health_synthesis_response`
- `portfolio_quant_metrics` -> `get_portfolio_quant_metrics_response`

Audited and excluded in v1:

- `get_portfolio_lot_detail_response` (lot-level granularity is beyond v1 chat need)
- `get_portfolio_transactions_response` direct event list (unbounded event detail risk)
- `get_portfolio_quant_report_html_content` (artifact payload not needed for chat grounding)
- Any direct access to `app/pdf_persistence/models.py` raw payload/provenance fields
- Any direct SQL tool exposed to the model

Tool invocation envelope:

- Per request, at most `6` tool invocations.
- Tool outputs in model context must be compacted to factual aggregates, with explicit `as_of_ledger_at` evidence metadata.
- Any unavailable required tool context must produce explicit blocked/unavailable responses; no fabricated fill-ins.

### 1.2 Copilot request/response contract freeze

Request contract (v1):

- `messages`: bounded prior turns (max `8`), role-limited to `user|assistant`
- latest user message max length: `2000` chars
- optional analysis scope fields:
  - `period`: one of `30D|90D|252D|MAX`
  - `scope`: `portfolio|instrument_symbol`
  - `instrument_symbol` required when `scope=instrument_symbol`
- optional operation selector:
  - `chat` (default)
  - `opportunity_scan`

Response contract (v1):

- `state`: `ready|blocked|error`
- `answer_text`: assistant response text (non-empty only when `state=ready`)
- `evidence`: list of source references, each with tool id plus key metric/context identifiers
- `limitations`: explicit caveats and non-advice posture
- `reason_code`: required when `state` is `blocked` or `error`

State/reason mapping freeze:

- `blocked`: `boundary_restricted`, `insufficient_context`, `provider_blocked_policy`
- `error`: `rate_limited`, `provider_misconfigured`, `provider_unavailable`

### 1.3 Deterministic opportunity-scanner freeze

Scanner objective:

- Produce deterministic ranked watchlist/addition candidates first.
- Use AI only for explanation text after ranking is finalized.

Frozen v1 rule inputs:

- `starter_100_symbols` from `app/market_data/symbol_universe.v1.json`
- current held symbols from `portfolio_summary`
- persisted USD day-level history from `list_price_history_for_symbol`
- optional portfolio context from `portfolio_risk_estimators` (for caveat text only; not rank randomization)

Eligibility filters (must all pass):

- symbol is in `starter_100_symbols`
- symbol is not currently held
- at least `90` valid USD daily close rows are available
- latest close is positive and timestamped

Ranking score (deterministic, descending):

- `discount_score`: normalized distance from rolling 90-day high
- `momentum_score`: normalized 30-day return
- `stability_score`: inverse normalized 30-day return volatility
- final `opportunity_score = 0.45 * discount_score + 0.35 * momentum_score + 0.20 * stability_score`
- tie-breakers in order: higher `discount_score`, then alphabetic symbol asc

Insufficient-data rejection semantics:

- If fewer than `20` eligible symbols remain after filters, return `state=blocked`, `reason_code=insufficient_context`.
- If any required input source is unavailable, return `state=blocked`, `reason_code=insufficient_context`.
- No partial ranking from incomplete candidate metrics.

### 1.4 Groq adapter contract freeze

Provider boundary:

- One Groq OpenAI-compatible chat-completions adapter only.
- Endpoint contract: `POST /openai/v1/chat/completions` on Groq base URL.
- No fallback provider chain in v1.

Configuration source freeze:

- required secret: `GROQ_API_KEY`
- required selected model id: `PORTFOLIO_AI_COPILOT_MODEL`
- required allowlist source: `PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST` (CSV or parsed list in config)
- adapter timeout seconds: `PORTFOLIO_AI_COPILOT_TIMEOUT_SECONDS` (default freeze target `20`)
- adapter max retries: `PORTFOLIO_AI_COPILOT_MAX_RETRIES` (default freeze target `1`)

Adapter request policy freeze:

- non-streaming request/response in v1
- single completion per request (`n=1`)
- reject unsupported/unsafe adapter parameters before provider call
- reject model ids not in allowlist with `provider_misconfigured`

Provider failure normalization freeze:

- provider `429` -> `error` + `rate_limited`
- provider `403` policy/permission/spend blocks -> `blocked` + `provider_blocked_policy`
- missing/invalid credentials or invalid model config -> `error` + `provider_misconfigured`
- provider timeout / 5xx / transport failures -> `error` + `provider_unavailable`

## Risks / Trade-offs

- [Risk] Model answers can overstate confidence or drift from source data.
  Mitigation: require evidence references, explicit limitations, and safe failure when tool context is insufficient.

- [Risk] Users may mistake explanation for execution-ready financial advice.
  Mitigation: keep deterministic scoring separate from narration, render non-advice messaging, and reject execution/guarantee requests explicitly.

- [Risk] Provider integration can add latency or runtime instability.
  Mitigation: keep v1 non-streaming, bound tool count/history size, and fail fast when provider configuration or responses are invalid.

- [Risk] Provider quota/policy restrictions can appear as sudden user-facing failures.
  Mitigation: freeze blocked/error reason mapping, add operator runbook coverage (project keys, spend limits, model permissions), and log provider status metadata.

- [Risk] AI work can sprawl into broad platform concerns.
  Mitigation: keep the change scoped to one backend slice, one frontend surface, one provider adapter boundary, and no vector store or memory infrastructure.

## Migration Plan

1. Finalize OpenSpec artifacts for the read-only copilot and opportunity-scanner scope, including Groq contract limits and reason-code mapping.
2. Add fail-first backend/frontend tests for chat contracts, safety boundaries, evidence rendering, and opportunity-scan states.
3. Implement backend AI slice with typed route, schemas, tool registry, provider adapter, and deterministic opportunity-scanner service.
4. Implement frontend copilot route with explicit guardrails, answer/evidence rendering, and deterministic opportunity-result presentation.
5. Update product/docs/changelog artifacts and validate touched-scope quality gates.

Rollback strategy:

- Remove the copilot route from the frontend workspace and disable the backend AI router while leaving existing portfolio analytics routes unchanged.

## Open Questions

None.
