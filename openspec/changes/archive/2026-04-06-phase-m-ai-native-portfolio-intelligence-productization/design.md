## Context

The current repository already ships deterministic portfolio analytics, risk estimators, Monte Carlo diagnostics, `portfolio_ml` signal/forecast contracts, and a read-only copilot route. However, the first-product experience remains pipeline-first and does not present a coherent "AI-native portfolio intelligence" operating model.

This phase closes that gap by introducing one explicit layered design:

1. **System of record layer**: canonical ingestion, ledger truth, persisted market snapshots (already in place).
2. **Decision layer**: command-center, risk/exposure decomposition, optimization comparison, anomaly/cluster diagnostics, and news context.
3. **AI copilot layer**: grounded narrative and guided question workflows on top of typed decision-layer tools.

External reference inputs (product SOT for this phase):

- `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/ghostfolio`
- `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/investbrain`
- `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/portfolio-gpt`

Reference extraction for decisions:

- Ghostfolio contributes product clarity and wealth-dashboard framing.
- Investbrain contributes "chat with your holdings" grounded interaction posture.
- PortfolioGPT contributes high-value natural-language question framing and holdings+news context coupling.

Constraints:

- Keep deterministic fail-fast posture and typed contracts.
- Keep read-only/non-execution boundary for analytics and copilot.
- Preserve strict logging and request-correlation conventions.
- Avoid broad architecture rewrites that disrupt current vertical slices.

## Goals / Non-Goals

**Goals:**

- Productize existing analytics/ML/copilot primitives into a decision-first user experience.
- Add missing decision capabilities: explicit exposure/risk decomposition, rebalancing strategy comparison, behavioral segmentation, anomaly surfacing, and holdings-linked news context.
- Standardize copilot answers around grounded evidence and bounded high-value question packs.
- Establish a frontend information architecture that makes first-viewport decisions obvious.
- Keep model governance auditable for every added ML family.

**Non-Goals:**

- Trade execution, automated order routing, or autonomous rebalance execution.
- Financial-advice guarantees, target-price certainty claims, or return promises.
- Deep-learning/RL-driven strategy systems in this phase.
- Multi-agent orchestration platform expansion.
- Replacing canonical ingestion/ledger architecture.

## Decisions

### Decision: Keep the deterministic ledger-first core and add product layers on top

We will not re-platform existing pipeline/ledger slices. New capabilities consume existing persisted truth through typed service boundaries.

Rationale:

- Preserves reliability and current delivery velocity.
- Avoids regressions from broad architecture churn.
- Keeps AI outputs grounded in auditable deterministic data.

Alternatives considered:

- Rebuild to an assistant-first architecture: rejected due high migration risk and weaker data-truth posture.

### Decision: Introduce three new domain slices for productization gaps

New backend slices:

- `app/portfolio_decision_command_center/`
- `app/portfolio_rebalancing/`
- `app/portfolio_news_context/`

These slices aggregate existing analytics and add bounded new computation APIs.

Rationale:

- Keeps vertical-slice ownership explicit.
- Prevents `portfolio_analytics` and `portfolio_ml` from becoming monolithic.

Alternatives considered:

- Add all behavior to existing analytics module: rejected due coupling and maintainability risk.

### Decision: Freeze v1 rebalancing strategy allowlist to `MVO`, `HRP`, `Black-Litterman`

The rebalancing studio exposes deterministic comparison outputs only (weights, expected return/risk, concentration deltas, assumptions).

Rationale:

- Aligns with requested roadmap while keeping scope bounded.
- Supports explainability and chart-ready outputs.

Alternatives considered:

- Include advanced optimizers and execution links immediately: rejected for scope and governance complexity.

### Decision: Extend ML family policy with segmentation/anomaly/quantile forecasting

Add governed families:

- Behavioral clustering (`KMeans`)
- Anomaly detection (`IsolationForest`)
- Quantile-capable boosting forecasts (interval-first outputs)

Rationale:

- Matches user-requested explainable ML direction.
- Preserves deterministic policy and champion governance posture.

Alternatives considered:

- Add LSTM/Prophet now: rejected by existing non-goal policy and explainability concerns.

### Decision: Copilot responses adopt one mandatory structured narrative envelope

Copilot responses will include:

- `answer`
- `evidence`
- `assumptions`
- `caveats`
- `suggested_follow_ups`

Question-pack entry points will be curated for concrete portfolio workflows.

Rationale:

- Reduces generic chatbot behavior.
- Improves trust and auditability for financial interpretation.

Alternatives considered:

- Keep free-form response only: rejected due weak explainability posture.

### Decision: Frontend IA migrates to decision lenses with route budgets

Primary lens posture:

- `Dashboard` (command center)
- `Holdings`
- `Performance`
- `Risk`
- `Rebalancing`
- `Copilot`
- `Transactions` (ledger trace)

Each lens keeps one first-viewport dominant job and bounded module count.

Rationale:

- Improves scannability and decision speed.
- Aligns with Ghostfolio-style clarity while preserving current app strengths.

Alternatives considered:

- Keep current route map with incremental widget additions: rejected because cognitive overload persists.

## Risks / Trade-offs

- [Scope expansion across backend + frontend + ML governance] -> Mitigate with phased task groups, fail-first tests, and explicit non-goals.
- [Performance regressions from added analytics modules] -> Mitigate with bounded windows, payload budgets, and route-level loading states.
- [Model drift or overconfident ML narratives] -> Mitigate with governance gates, stale/unavailable states, interval-first outputs, and caveat requirements.
- [News-context hallucination risk] -> Mitigate with source-provenance metadata and strict unknown-context fallback copy.
- [IA migration confusion for existing users] -> Mitigate with route compatibility redirects and explicit lens labels during transition.

## Migration Plan

1. Add fail-first contract tests for new and modified capabilities (backend + frontend).
2. Implement backend decision-layer endpoints and typed schemas for command-center, rebalancing, and news context.
3. Extend `portfolio_analytics` and `portfolio_ml` contracts for exposure, contribution-to-risk, clustering, anomalies, and quantile forecast outputs.
4. Extend copilot orchestration and response schema for structured narrative envelope and question packs.
5. Refactor frontend route composition into decision lenses and add visualization modules (drawdown, contribution-to-risk, correlation, frontier comparison, anomaly timeline, forecast intervals).
6. Align docs and product narrative (`README`, `docs/product/*`, changelog) with new capability posture.
7. Run full validation gates before handoff.

Rollback strategy:

- Keep existing analytics and copilot routes operable as compatibility baseline.
- Feature-flag new command-center/rebalancing/news surfaces.
- Revert per-slice if regressions appear, without altering ledger or ingestion contracts.

## Open Questions

- Which news providers and licensing posture are approved for holdings-linked context in local-first mode?
- Should `Black-Litterman` user views be exposed only through heuristic posture presets in v1, or with explicit matrix/view inputs?
- What default benchmark set is canonical for command-center comparisons (`SPY`, `60/40`, `BTC`) and how is benchmark availability validated by scope?
