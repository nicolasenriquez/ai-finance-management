## Context

Current repository strengths are deterministic accounting, market-data boundaries, strict typing, and read-only analytics contracts. The reference sets provide broad idea coverage:

- `references/timeseries-analysis`: ARIMA/SARIMA, Holt methods, decomposition, and forecasting workflows.
- `references/ml-finance-analysis`: ridge/SVR/LSTM stock prediction and clustering/autoencoder notebooks.

Those references are educational and broad, but not directly production-ready for this codebase because they rely on notebook assumptions, weak governance, and in some cases non-portfolio domains.

This design narrows scope to what brings immediate value:

- deterministic signals for current portfolio monitoring
- CAPM metrics as deterministic portfolio-management signals
- statistically grounded baseline forecasting with explicit quality gates
- auditable model governance metadata

## Goals / Non-Goals

**Goals:**
- Add deterministic time-series signal extraction for portfolio and instrument scopes.
- Add CAPM metrics (`beta`, `alpha`, expected return, market premium) with explicit benchmark and risk-free provenance.
- Add baseline forecasting workflows with walk-forward validation and measurable baseline comparison.
- Add explicit champion promotion logic and stale/unavailable semantics.
- Persist enough metadata to audit training data windows, feature provenance, and quality outcomes.
- Keep the phase read-only and safe for downstream analytics consumption.
- Bridge `portfolio_ml` outputs into read-only copilot orchestration using typed allowlisted tools and evidence references.
- Define a governed copilot SQL analytics contract limited to allowlisted read-only templates, strict parameter validation, and auditable execution metadata.
- Define attachment-by-reference chat semantics (`document_id` list) and prompt-suggestion response metadata to prepare frontend chat improvements without introducing UI redesign into this phase.

**Non-Goals:**
- Production LSTM/RNN or Prophet deployment in this phase.
- Customer segmentation from non-portfolio domains.
- Intraday execution, rebalancing automation, broker routing, or guaranteed-return advice.
- Real-time online training or scheduler/queue expansion for v1.
- Free-form or user-authored SQL execution in copilot.
- Binary file upload handling inside copilot chat endpoints.
- Copilot UX shell redesign (lateral dock, launcher behavior, and panel choreography remain in `phase-j`).

## Decisions

### Decision 1: Build one dedicated `portfolio_ml` vertical slice
- Decision: Add `app/portfolio_ml/` with isolated routes, schemas, services, and tests.
- Rationale: keeps ML lifecycle separate from deterministic accounting and existing analytics computation paths.
- Alternatives considered:
  - extend `app/portfolio_analytics/` directly: rejected due to mixed responsibilities and higher regression risk.
  - add notebook-only workflow: rejected because no enforceable API, tests, or governance contract.

### Decision 2: Start with deterministic signals plus baseline model family only
- Decision: Include signal builders and baseline forecast models (naive, seasonal-naive, EWMA/Holt, ARIMA, ridge-lag regression).
- Rationale: these techniques are interpretable, cheaper to validate, and align with current operational maturity.
- Alternatives considered:
  - start with LSTM/RNN from references: rejected due to higher complexity and weaker explainability/governance in v1.
  - start with Prophet: rejected due to dependency and tuning complexity before baseline quality gates are established.

### Decision 3: Implement CAPM as deterministic signal contract, not as forecast model
- Decision: CAPM outputs are produced in signal endpoints using explicit benchmark and risk-free inputs and annualization metadata.
- Rationale: CAPM is useful for portfolio management explainability and risk decomposition, and it aligns with deterministic read-only contracts.
- Alternatives considered:
  - treat CAPM as part of forecasting champion selection: rejected because CAPM is explanatory/risk model, not horizon forecast candidate.
  - infer benchmark or risk-free silently when missing: rejected due to fail-fast and provenance requirements.

### Decision 4: Require walk-forward evaluation with explicit promotion thresholds
- Decision: Only publish a champion forecast snapshot when candidate quality exceeds naive baseline by policy thresholds and passes calibration checks.
- Rationale: avoids shipping decorative forecasts that underperform simple baselines.
- Alternatives considered:
  - publish best model regardless of baseline: rejected because it can degrade quality silently.
  - manual analyst promotion without metrics: rejected because it breaks deterministic governance.

### Decision 5: Expose probabilistic read-only forecast contracts with lifecycle states
- Decision: API returns horizon-level point + interval outputs and one state in `ready|unavailable|stale|error`.
- Rationale: downstream consumers need confidence context and cannot infer validity from nullable fields.
- Alternatives considered:
  - point forecast only: rejected due to false precision risk.
  - return zeroes/last-known values on failure: rejected by fail-fast policy.

### Decision 6: Persist model-run metadata and provenance hash in registry snapshots
- Decision: save training/eval metadata (data window, feature hash, metric vector, baseline comparator, expiry) as auditable snapshots.
- Rationale: gives reproducibility and policy traceability without introducing heavy model-serving infrastructure.
- Alternatives considered:
  - no persistence beyond logs: rejected because logs are insufficient for deterministic audit and rollback.
  - full external model platform integration: rejected as over-scope for current phase.

### Decision 7: Keep training offline/command-triggered in v1
- Decision: training/evaluation runs as explicit command workflow; prediction APIs read latest approved snapshot only.
- Rationale: minimizes operational complexity and aligns with current data-sync command posture.
- Alternatives considered:
  - automatic retraining scheduler: rejected for now because scheduling and orchestration are deferred in product scope.

### Decision 8: Integrate `portfolio_ml` into copilot through allowlisted read-only tool adapters
- Decision: add explicit copilot tool adapters for time-series signals, CAPM payloads, forecast horizons, and model-governance summaries; keep tool execution bounded and evidence-attributed.
- Rationale: this delivers immediate ML-to-copilot product value without exposing raw model internals or bypassing existing guardrails.
- Alternatives considered:
  - defer all copilot integration to later phase: rejected because this would postpone practical usability of new ML outputs.
  - expose raw `portfolio_ml` tables to provider context: rejected due to privacy, determinism, and contract-drift risk.

### Decision 9: Govern copilot SQL through template IDs, not free-form query text
- Decision: add one read-only SQL tool that executes only allowlisted template IDs with typed parameters, row limits, timeout caps, and execution audit metadata.
- Rationale: operators gain useful calculated views while preserving fail-fast controls and eliminating arbitrary query risk.
- Alternatives considered:
  - allow free-form SQL entered by users: rejected due to safety and data-governance concerns.
  - avoid SQL tools entirely: rejected because curated query templates are a practical bridge for high-value aggregated diagnostics.

### Decision 10: Use document attachments by reference only
- Decision: extend copilot request contracts with bounded `document_id` references that must resolve to previously ingested documents; no multipart upload path in copilot chat.
- Rationale: keeps chat stateless, avoids binary transport complexity, and reuses existing ingestion trust controls.
- Alternatives considered:
  - add raw file upload support directly to copilot route: rejected as contract coupling and security scope expansion.
  - ignore document context in copilot: rejected because users need document-grounded follow-up in later UX phases.

### Decision 11: Include backend prompt-suggestion metadata now, render UX later
- Decision: extend copilot response contract with optional prompt suggestions generated from active scope/tool context and lifecycle state.
- Rationale: frontend can adopt suggestion chips incrementally without reworking backend semantics later.
- Alternatives considered:
  - keep suggestion generation frontend-only: rejected because backend has more reliable context about active tools, states, and unavailable reasons.

## Risks / Trade-offs

- [Risk] Forecast quality may degrade in sparse symbol history windows.
  Mitigation: enforce minimum history thresholds and explicit `unavailable` responses.

- [Risk] CAPM outputs can be misleading when benchmark or risk-free source is stale/missing.
  Mitigation: require explicit source metadata and return `unavailable` with factual reason when required CAPM inputs are missing.

- [Risk] Overfitting from feature leakage in walk-forward pipelines.
  Mitigation: add fail-first leakage tests and strict train/test temporal boundary checks.

- [Risk] Model confidence intervals may be misread as guarantees.
  Mitigation: include explicit non-advice/uncertainty messaging and confidence metadata in contracts.

- [Risk] New dependencies increase maintenance burden.
  Mitigation: lock dependency versions and start with smallest model family that yields measurable value.

- [Risk] Governed SQL template surface can expand into de-facto free-form analytics.
  Mitigation: enforce template-id allowlist, read-only transaction isolation, max-row caps, and structured audit logs for each execution.

- [Risk] Document references can leak unsupported raw context into prompt assembly.
  Mitigation: allow only validated ingestion IDs, apply explicit redaction/minimization policy, and fail closed on unresolved or unauthorized references.

## Migration Plan

1. Freeze included model/signal scope and deferred-technique list from references.
2. Add fail-first tests for feature determinism, CAPM computation semantics, walk-forward evaluation, and promotion policy.
3. Implement `portfolio_ml` services and registry persistence.
4. Expose read-only APIs for signals, forecasts, and registry audit.
5. Extend copilot contracts/services for ML tool grounding, governed SQL templates, document-reference inputs, and prompt-suggestion outputs.
6. Update docs/changelog and run full touched-scope validation gates.

Rollback strategy:

- Disable `portfolio_ml` router and keep existing `portfolio_analytics` endpoints unchanged.
- Retain persisted model snapshots for audit but stop serving forecast outputs.

## Open Questions

None.
