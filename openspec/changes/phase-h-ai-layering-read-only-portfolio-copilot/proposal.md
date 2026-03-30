## Why

The repository now has the core ingredients AI actually needs to be useful: persisted ledger truth, market-data boundaries, typed analytics contracts, and a stable frontend workspace. The next leverage point is not broad agentic automation, but a narrow read-only copilot that can explain portfolio movement, answer questions from aggregated analytics, and surface guardrailed research candidates without exposing raw private records or pretending to execute trades.

## What Changes

- Add a read-only backend portfolio copilot contract that accepts portfolio questions, uses an allowlisted set of aggregated analytics tools, and returns grounded answers with explicit limitations.
- Add a deterministic opportunity-scanner workflow that computes candidate additions or "discount" ideas from explicit rules first, then lets AI narrate the result in plain language.
- Add a dedicated frontend copilot workspace surface for chat, evidence-backed explanations, and opportunity-scan results with visible privacy and non-advice guardrails.
- Freeze AI safety boundaries for v1: no direct SQL/database agent access, no raw canonical PDF payload access, no trade execution, no order routing, and no silent fallback when required context is unavailable.
- Add fail-first validation coverage for tool orchestration, privacy boundaries, prompt/tool regressions, and grounded-response behavior before implementation begins.

## Capabilities

### New Capabilities
- `portfolio-ai-copilot`: Read-only backend AI assistant contracts, tool orchestration rules, privacy boundaries, and deterministic opportunity-scan behavior for the portfolio domain.
- `frontend-ai-copilot-workspace`: Dedicated frontend copilot experience for chat, evidence rendering, and opportunity-scan presentation within the portfolio workspace.

### Modified Capabilities
- None.

## Impact

- Backend: new AI-focused vertical slice under `app/` plus API routes, schemas, service orchestration, and tests; no direct changes to canonical, ledger, or market-data persistence boundaries should be required.
- Frontend: new workspace route or panel, typed client contracts, response rendering states, and explicit disclaimer/evidence UX.
- Dependencies: likely a single approved model-provider SDK plus minimal adapter/config wiring; no vector database, scheduler, or multi-agent framework in v1.
- Governance: roadmap/backlog updates, OpenSpec specs/tasks, operator-facing guardrails, and changelog evidence.
