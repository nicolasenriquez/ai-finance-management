## 1. Contract Baseline and Fail-First Coverage

- [x] 1.1 Add fail-first backend contract tests for new command-center, exposure, contribution-to-risk, correlation, rebalancing, and news-context endpoints.
- [x] 1.2 Add fail-first backend tests for clustering/anomaly payload determinism and quantile-forecast interval contract requirements.
- [x] 1.3 Add fail-first copilot tests for structured narrative envelope (`answer`, `evidence`, `assumptions`, `caveats`, `suggested_follow_ups`) and question-pack behavior.
- [x] 1.4 Add fail-first frontend route-composition tests for decision-lens navigation and dashboard first-viewport budget behavior.

## 2. Decision-Layer Backend APIs

- [x] 2.1 Implement `portfolio-decision-command-center` slice with typed schemas and read-only service orchestration.
- [x] 2.2 Extend `portfolio-analytics` with explicit exposure-decomposition contracts and route handlers.
- [x] 2.3 Extend `portfolio-analytics` with contribution-to-risk datasets and methodology metadata.
- [x] 2.4 Extend `portfolio-analytics` with bounded correlation-matrix contracts and guardrail failure semantics.
- [x] 2.5 Ensure all new decision-layer responses include explicit as-of/freshness metadata and fail-fast unavailable states.

## 3. Rebalancing and News Context Capabilities

- [x] 3.1 Implement `portfolio-rebalancing-studio` slice for `MVO`, `HRP`, and `Black-Litterman` strategy comparison outputs.
- [x] 3.2 Implement typed scenario-constraint validation and infeasible-state failure semantics for rebalancing workflows.
- [x] 3.3 Implement `portfolio-news-context` slice with holdings-grounded symbol mapping and source-provenance metadata.
- [x] 3.4 Implement bounded news-summary generation with explicit caveats and non-advice framing.
- [x] 3.5 Add integration tests proving rebalancing/news endpoints remain read-only and deterministic for equivalent input state.

## 4. ML and Governance Extensions

- [x] 4.1 Extend `portfolio-timeseries-signals` with deterministic clustering outputs and lifecycle metadata.
- [x] 4.2 Extend `portfolio-timeseries-signals` with anomaly-event contracts and severity/freshness metadata.
- [x] 4.3 Extend `portfolio-forecasting-baselines` candidate policy to include quantile-boosting family and interval-calibration gates.
- [x] 4.4 Update forecast response contracts to publish percentile intervals (`p10`, `p50`, `p90` or explicit quantile equivalent) per horizon.
- [x] 4.5 Extend `portfolio-ml-model-governance` registry behavior for segmentation/anomaly family lineage, freshness, and policy-version auditability.

## 5. Copilot and Frontend Productization

- [x] 5.1 Update copilot backend orchestration to produce structured narrative envelope and evidence-linked what-changed explanations.
- [x] 5.2 Implement guided question-pack selection by decision lens and scope context.
- [x] 5.3 Refactor frontend workspace navigation into decision lenses (`Dashboard`, `Holdings`, `Performance`, `Risk`, `Rebalancing`, `Copilot`, `Transactions`) with migration-safe route compatibility.
- [x] 5.4 Implement dashboard command-center first-viewport layout, insight cards, and what-changed panel.
- [x] 5.5 Implement risk/rebalancing visualization modules (correlation, contribution-to-risk, frontier/scenario comparison, anomaly timeline, forecast intervals) with explicit lifecycle states.
- [x] 5.6 Update copilot UI to render structured response sections and handoff affordances into dashboard/news/risk modules.

## 6. Governance, Documentation, and Validation

- [x] 6.1 Update `README.md` and `docs/product/*` to reflect AI-native decision-layer product posture and capabilities.
- [x] 6.2 Add changelog entries with phase scope, endpoints/contracts added, and evidence references.
- [x] 6.3 Run backend validation gates for touched modules (`pytest`, `mypy`, `pyright`, `ty`, `ruff`, `black --check`).
- [x] 6.4 Run frontend validation gates for touched modules (`lint`, `type-check`, `test`, `build`).
- [x] 6.5 Re-run OpenSpec validation/status checks and capture implementation handoff notes with residual risks and follow-up items.
