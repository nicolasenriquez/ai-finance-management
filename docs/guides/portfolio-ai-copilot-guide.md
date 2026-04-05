# Portfolio AI Copilot Guide

## Purpose

This guide defines the shipped v1 AI-layer contract for the read-only portfolio
copilot, including safety boundaries, provider configuration, and validation
expectations.

## Shipped Scope (Phase H)

- Backend route: `POST /api/portfolio/copilot/chat`
- Frontend route: `/portfolio/copilot`
- Supported operations:
  - `chat`
  - `opportunity_scan`
- Request bounds:
  - max prior turns: `8`
  - max user message length: `2000`
  - max tool calls: `6`
- Typed response states:
  - `ready`
  - `blocked`
  - `error`
- Stable reason codes:
  - `boundary_restricted`
  - `insufficient_context`
  - `provider_blocked_policy`
  - `rate_limited`
  - `provider_misconfigured`
  - `provider_unavailable`

## Phase-I Extensions (Time-Series and Forecast Governance)

- Added `portfolio_ml` allowlisted evidence tools:
  - `portfolio_ml_signals`
  - `portfolio_ml_capm`
  - `portfolio_ml_forecasts`
  - `portfolio_ml_registry`
- Added governed SQL template tool path:
  - `portfolio_sql_template` (template-id allowlist only; no free-form SQL)
- Added bounded attachment-by-reference request field:
  - `document_ids` (validated against persisted ingestion records)
- Added optional response metadata:
  - `prompt_suggestions` (bounded follow-up prompts)

## Explicit Non-Goals

- no trade execution, order placement, or automatic rebalancing
- no guaranteed-return claims
- no direct SQL/database access from the model
- no raw canonical/source payload exposure to model context
- no vector store, RAG ingestion, or persistent chat memory in v1
- no fallback provider chain (Groq adapter only)
- no free-form SQL execution

## Provider Configuration (Groq)

Required environment variables:

- `GROQ_API_KEY`
- `PORTFOLIO_AI_COPILOT_MODEL`
- `PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST` (JSON array)

Optional bounded runtime controls:

- `PORTFOLIO_AI_COPILOT_TIMEOUT_SECONDS` (default `20`)
- `PORTFOLIO_AI_COPILOT_MAX_RETRIES` (default `1`)
- `PORTFOLIO_AI_COPILOT_GROQ_BASE_URL` (default `https://api.groq.com`)

Fail-fast policy:

- missing/invalid provider config is mapped to `provider_misconfigured`
- no silent fallback provider behavior is allowed

## Groq Operator Runbook Notes

- Use one project-scoped API key for this environment.
- Set conservative project spend limits before enabling public/shared use.
- Explicitly grant only approved model IDs and keep
  `PORTFOLIO_AI_COPILOT_MODEL_ALLOWLIST` aligned with those permissions.
- Rotate keys immediately if exposure is suspected.
- Treat repeated `provider_blocked_policy` or `rate_limited` responses as
  operator incidents (permissions/quota), not end-user retry-only issues.

## Privacy And Prompt-Minimization Rules

- Model context is assembled only from allowlisted aggregated analytics tools.
- Excluded markers are enforced before provider calls:
  - `raw_payload`
  - `source_payload`
  - `canonical_payload`
  - `transaction_events`
- Unsafe requests are explicitly blocked with `boundary_restricted`.
- Document references are validated by `document_id`; unresolved references are rejected
  before provider invocation.

## Governed SQL Policy

- SQL execution is template-based and allowlisted.
- Free-form SQL text is explicitly rejected (`governed_sql_policy` semantics).
- One bounded template is available in this slice:
  - `portfolio_ml_latest_forecast_states`
- Parameter validation and row bounds are enforced before execution.
- Response metadata includes template ID, bounded row count, timeout bound, and
  audit identifier.

## Validation Expectations

Backend contract/safety/provider/opportunity tests:

```bash
uv run pytest -v app/portfolio_ai_copilot/tests
```

Focused phase-i copilot extensions:

```bash
uv run pytest -v app/portfolio_ai_copilot/tests/test_ml_contract_extensions_fail_first.py
uv run pytest -v app/portfolio_ai_copilot/tests/test_governed_sql_template_policy_fail_first.py
```

Frontend copilot route/workspace tests:

```bash
npm --prefix frontend run test -- src/app/copilot-workspace.contract.fail-first.test.ts src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx
```

Full frontend gates:

```bash
npm --prefix frontend run lint
npm --prefix frontend run test
npm --prefix frontend run build
```

OpenSpec validation:

```bash
openspec validate phase-h-ai-layering-read-only-portfolio-copilot --type change --strict --json
openspec validate --specs --all --json
```
