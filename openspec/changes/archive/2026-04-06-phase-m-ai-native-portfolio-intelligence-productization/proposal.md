## Why

As of April 6, 2026, the repository runtime already includes risk, quant, ML, and copilot primitives, but the product narrative and first-contact UX still read as a deterministic data pipeline rather than an AI-native portfolio decision product. We need a phase that productizes existing capabilities and fills targeted gaps (news context, rebalancing strategies, clustering/anomaly diagnostics) so users can answer "what changed, why, and what to do next" from one coherent workspace.

## What Changes

- Reframe the product around a decision-first portfolio command center that foregrounds net worth, return posture, drawdown, concentration, benchmark context, and explainable daily insights.
- Add a dedicated rebalancing studio with deterministic scenario comparison and explicit optimization strategy contracts (`MVO`, `HRP`, `Black-Litterman`) without execution side effects.
- Add a holdings-grounded market-news context layer with explicit provenance, freshness, and uncertainty semantics.
- Extend analytics contracts with explicit exposure, correlation, and contribution-to-risk payloads aligned to portfolio decision workflows.
- Extend ML contracts with deterministic behavioral segmentation (`KMeans`), anomaly surfacing (`IsolationForest`), and governed interval-forward forecasting enhancements (quantile boosting family).
- Evolve copilot from generic Q&A posture into a portfolio copilot workflow with bounded high-value question packs (for example: "why is my portfolio down today?") and explicit evidence/assumption/caveat response framing.
- Reorganize frontend workspace information architecture into decision lenses that prioritize first-viewport outcomes over route-level module sprawl.
- Keep fail-fast, read-only, and non-advice boundaries unchanged: no autonomous execution, no guaranteed-return claims, and no hidden fallbacks.

## Capabilities

### New Capabilities
- `portfolio-decision-command-center`: Decision-first dashboard contract for net worth, return/risk posture, concentration, and explainable operating insights.
- `portfolio-rebalancing-studio`: Deterministic portfolio rebalancing and strategy-comparison contracts for `MVO`, `HRP`, and `Black-Litterman` outputs.
- `portfolio-news-context`: Holdings-linked market context contract with freshness metadata and explainable summarization boundaries.

### Modified Capabilities
- `portfolio-analytics`: Add decision-layer contracts for benchmark context, exposure decomposition, correlation, and contribution-to-risk outputs.
- `portfolio-ai-copilot`: Add question-pack orchestration and structured answer framing (`answer`, `evidence`, `assumptions`, `caveats`, `suggested_follow_ups`).
- `portfolio-timeseries-signals`: Add clustering and anomaly contracts for deterministic behavior segmentation and outlier surfacing.
- `portfolio-forecasting-baselines`: Expand approved v1 family with quantile-capable boosting outputs while preserving interval-first semantics.
- `portfolio-ml-model-governance`: Extend governance policy to include clustering/anomaly/quantile-forecast model families and promotion rules.
- `frontend-analytics-workspace`: Enforce decision-lens IA and chart hierarchy budgets for command center, risk lab, and rebalancing workflows.
- `frontend-ai-copilot-workspace`: Promote guided question packs, evidence trace panels, and what-changed narratives in copilot UX.

## Impact

- Backend slices: `app/portfolio_analytics/`, `app/portfolio_ml/`, `app/portfolio_ai_copilot/`, plus new slices for command-center/rebalancing/news context.
- Frontend workspace routes and shared primitives under `frontend/src/pages/`, `frontend/src/features/portfolio-workspace/`, and `frontend/src/features/portfolio-copilot/`.
- API surface expansion for risk/exposure/rebalancing/news/ML diagnostics endpoints and typed schema updates.
- ML dependency and governance impact for `scikit-learn` clustering/anomaly/quantile candidate paths, with strict deterministic and fail-fast controls.
- Product/docs alignment updates (`README.md`, `docs/product/*`, changelog, and workspace guidance).
- Reference posture (SOT inputs for product direction):
  - `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/ghostfolio`
  - `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/investbrain`
  - `/Users/NicolasEnriquez/Desktop/AI Finance Mgmt/references/portfolio-gpt`
