## Context

The repository has a stable frontend baseline for grouped summary and lot-detail screens, with documented accessibility and Core Web Vitals evidence, but the user experience remains table-first. Product direction now requires a dashboard-grade analytics workspace (home + analytics + risk + transactions), chart-driven insights, and explicit risk estimators before proceeding to broader database hardening work.

Current constraints:

- Backend contract is authoritative and read-only for analytics routes.
- Financial calculations must remain deterministic and decimal-safe.
- Frontend behavior must remain fail-fast with explicit unsupported/error states.
- Existing frontend quality gates (WCAG/CWV/tests) must continue to pass.
- Framework migration (Next.js) is optional and currently unapproved.

## Goals / Non-Goals

**Goals:**

- Extend portfolio analytics APIs with chart-ready time-series and attribution/risk inputs.
- Deliver a multi-route analytics workspace with deterministic navigation and trust/provenance context.
- Add an explicit risk-estimator capability with documented formulas and bounded behavior.
- Preserve current summary/lot-detail contracts while layering dashboard usability and visual analytics.
- Keep implementation aligned with repository standards while using `ultimate-react-course` as pattern reference.

**Non-Goals:**

- Full framework migration from Vite to Next.js in this change.
- Authentication or multi-user role workflows.
- FX-sensitive or multi-currency valuation expansion beyond approved boundaries.
- Scheduler/queue architecture changes for market refresh operations.
- Replacing ledger-first truth with client-side inferred calculations.

## Decisions

### 1. Keep `React + Vite` as implementation baseline for this phase

Decision:

- Execute the UX/analytics expansion on the current frontend stack.

Why:

- FastAPI-backed API-first architecture is already in place.
- Value delivery is blocked by analytics UX depth, not rendering framework limits.
- Framework migration now would increase risk and delay chart/risk delivery.

Alternative considered:

- Migrate to Next.js immediately.
- Rejected for this phase due to migration cost and unstable API expansion scope.

### 2. Introduce new analytics endpoints before chart-heavy UI rollout

Decision:

- Add typed, provenance-aware backend endpoints first, then build chart modules on top.

Why:

- Prevents frontend inference of unsupported metrics.
- Keeps formulas and data semantics in backend truth boundary.
- Reduces UX rework caused by late contract changes.

Alternative considered:

- Build charts from existing summary payload only.
- Rejected because it would force lossy client-side derivations and hidden assumptions.

### 3. Separate risk estimators as an explicit capability

Decision:

- Define risk metrics in a dedicated capability with formal requirements and failure behavior.

Why:

- Risk calculations carry higher interpretation risk than simple KPI cards.
- Dedicated capability keeps formulas, windows, and insufficiency behavior auditable.
- Enables incremental rollout and test isolation.

Alternative considered:

- Mix risk requirements into generic portfolio-analytics spec only.
- Rejected because it obscures scope and weakens traceability.

### 4. Preserve and extend release-readiness gates for chart routes

Decision:

- Update frontend release-readiness requirements to include chart modules and new routes.

Why:

- Existing readiness spec is MVP-route scoped.
- New dashboard complexity can regress accessibility and interaction performance.
- Explicit gates prevent visual expansion from bypassing quality controls.

Alternative considered:

- Keep existing readiness spec unchanged.
- Rejected because it leaves the new routes ungoverned.

### 5. Adopt a pinned quant dependency stack and reject non-v1 finance libraries

Decision:

- Use a narrow, approved quant stack for v1 estimator computation: `numpy`, `pandas`, and `scipy`.
- Allow `pandas-ta` only for optional analytics overlays in UI-facing modules; it is not canonical for risk-estimator truth.
- Pin approved quant dependencies in repository dependency manifests/lockfiles to keep estimator output reproducible.
- Reject the following packages for this phase: `zipline`, `zipline-reloaded`, `pyfolio`, `pyrisk`, `mibian`, `backtrader`, `QuantLib-Python`.

Why:

- v1 needs deterministic risk estimators, not full backtesting engines or derivatives-pricing frameworks.
- The rejected set adds maintenance/runtime complexity, stale ecosystem risk, or domain mismatch for the current scope.
- A narrow stack aligns with strict typing, fail-fast behavior, and YAGNI.

Alternative considered:

- Adopt the entire external finance-package longlist as first-class runtime dependencies.
- Rejected due to unnecessary operational surface area and weaker reproducibility guarantees.

### 6. Enforce an operations-first finance computation contract for estimator pipelines

Decision:

- Use an operations-first sequence for estimator computation paths:
  1) validate sorted, timezone-aware series inputs
  2) apply explicit missing-data policy
  3) apply explicit frequency/calendar policy
  4) apply deterministic event-time alignment policy where asynchronous joins are required
  5) execute estimator math with explicit return basis and annualization basis metadata
- Keep pandas as the primary time-series/table computation layer, NumPy for numeric kernels, and SciPy for advanced statistics/optimization operations only when required by approved estimators.

Why:

- Most estimator drift comes from hidden data-preparation choices rather than formula symbols.
- This decision aligns implementation with the new NumPy/pandas/SciPy standards and reduces ambiguity in risk output interpretation.
- It provides a deterministic implementation checklist that is directly testable.

Alternative considered:

- Allow estimator implementations to choose per-endpoint preprocessing behavior ad hoc.
- Rejected because it causes silent methodology divergence across metrics and versions.

### 7. Freeze default estimator windows and methodology metadata for v1

Decision:

- Set v1 default evaluation windows to `30`, `90`, and `252` trading-day periods for rolling estimators unless endpoint-level capability explicitly states otherwise.
- Require estimator responses to expose methodology metadata at minimum: estimator id, return basis (`simple` or `log`), annualization basis, window length, and as-of timestamp.

Why:

- Window defaults are required to unblock frontend risk route design and backend test fixtures.
- Explicit methodology metadata avoids frontend guessing and improves auditability.

Alternative considered:

- Keep default windows unresolved for implementation-time negotiation.
- Rejected because it keeps API/UX contracts unstable and delays test fixture finalization.

### 8. Standardize chart foundation on `Recharts` for v1

Decision:

- Use `Recharts` as the default chart library for v1 analytics workspace routes.

Why:

- Faster implementation path for current React + Vite stack and current dashboard scope.
- Lower initial complexity for accessible chart composition and test setup.
- Sufficient feature set for v1 trend, contribution, and risk visual modules.

Alternative considered:

- Use `ECharts` as the default from the first slice.
- Rejected for v1 due to additional complexity/capability overhead not required by the initial chart set.

### 9. Freeze `Transactions` tab v1 scope to ledger events only

Decision:

- `Transactions` route v1 displays persisted ledger events only.
- Market-refresh operation diagnostics are explicitly deferred to a follow-up slice.

Why:

- Keeps route semantics aligned with portfolio truth boundaries.
- Prevents mixing operator/ops telemetry with user-facing transaction history in the first release.
- Reduces scope and contract coupling for this implementation phase.

Alternative considered:

- Include both ledger events and market-refresh diagnostics in first slice.
- Rejected because it introduces mixed-purpose UX and additional contract surface before dashboard baseline stabilizes.

### 10. Freeze chart-analytics period enum for v1 endpoints

Decision:

- Standardize v1 period enum for chart analytics endpoints to: `30D`, `90D`, `252D`, `MAX`.
- Reject unsupported period values explicitly with client-facing validation errors.

Why:

- Removes ambiguity from backend endpoint behavior and frontend filter controls.
- Enables deterministic fixtures and cross-route consistency in tests.
- Aligns time-series/contribution contracts with the estimator-window discipline already frozen for v1.

Alternative considered:

- Allow per-endpoint period lists or delayed period finalization.
- Rejected because it creates avoidable UI/API divergence and test instability.

## Risks / Trade-offs

- [Risk] Time-series/risk endpoint expansion may increase backend query cost. -> Mitigation: start with bounded periods, indexed filters, and deterministic query contracts.
- [Risk] Chart-heavy routes can regress INP/CLS and accessibility labeling. -> Mitigation: extend readiness gates and capture route-specific evidence before declaring completion.
- [Risk] Over-adopting course patterns could conflict with repo standards (typing/testing/security). -> Mitigation: treat course repo as pattern-reference SOT only; keep local standards authoritative.
- [Risk] Metric interpretation drift (drawdown/Sharpe/VaR assumptions). -> Mitigation: require explicit formula/provenance metadata and insufficiency rejection rules.
- [Risk] Estimator output drift caused by implicit preprocessing (sorting, timezone, missing-data, frequency, alignment). -> Mitigation: enforce operations-first preprocessing contract and regression fixtures tied to methodology metadata.
- [Risk] Chart-library mismatch with accessibility/performance constraints as chart complexity grows. -> Mitigation: start on `Recharts` and keep library-switch decision gated by explicit route-level performance evidence.

## Migration Plan

1. Define and merge spec deltas for:
   - `portfolio-analytics`
   - `frontend-release-readiness`
   - `frontend-analytics-workspace` (new)
   - `portfolio-risk-estimators` (new)
2. Implement backend analytics endpoint contracts and tests first.
3. Implement frontend route architecture and chart primitives.
4. Implement Home + Analytics + Risk + Transactions views incrementally with tests.
5. Implement estimator methodology metadata and regression fixtures (returns, volatility, drawdown, beta baseline).
6. Implement shared period enum validation (`30D`, `90D`, `252D`, `MAX`) across backend/frontend analytics filters and contracts.
7. Capture accessibility/CWV evidence for new routes and update docs/checklists.
8. Rollback strategy: if regressions occur, disable new routes behind feature-level router fallback and preserve existing summary/lot-detail screens unchanged.

## Open Questions

None.
