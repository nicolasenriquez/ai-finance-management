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
- Keep the change implementation-local, test-first, and compatible with current validation gates.

**Non-Goals:**
- Full migration to the external AI template or any multi-framework agent stack.
- Vector search, RAG ingestion, persistent conversation memory, or multi-agent orchestration.
- Trade execution, portfolio rebalancing automation, or guaranteed-return recommendations.
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
- Decision: Use a typed HTTP request/response contract with bounded conversation history and no required server-side conversation persistence in v1.
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

## Risks / Trade-offs

- [Risk] Model answers can overstate confidence or drift from source data.
  Mitigation: require evidence references, explicit limitations, and safe failure when tool context is insufficient.

- [Risk] Users may mistake explanation for execution-ready financial advice.
  Mitigation: keep deterministic scoring separate from narration, render non-advice messaging, and reject execution/guarantee requests explicitly.

- [Risk] Provider integration can add latency or runtime instability.
  Mitigation: keep v1 non-streaming, bound tool count/history size, and fail fast when provider configuration or responses are invalid.

- [Risk] AI work can sprawl into broad platform concerns.
  Mitigation: keep the change scoped to one backend slice, one frontend surface, one provider adapter boundary, and no vector store or memory infrastructure.

## Migration Plan

1. Finalize OpenSpec artifacts for the read-only copilot and opportunity-scanner scope.
2. Add fail-first backend/frontend tests for chat contracts, safety boundaries, evidence rendering, and opportunity-scan states.
3. Implement backend AI slice with typed route, schemas, tool registry, provider adapter, and deterministic opportunity-scanner service.
4. Implement frontend copilot route with explicit guardrails, answer/evidence rendering, and deterministic opportunity-result presentation.
5. Update product/docs/changelog artifacts and validate touched-scope quality gates.

Rollback strategy:

- Remove the copilot route from the frontend workspace and disable the backend AI router while leaving existing portfolio analytics routes unchanged.

## Open Questions

None.
