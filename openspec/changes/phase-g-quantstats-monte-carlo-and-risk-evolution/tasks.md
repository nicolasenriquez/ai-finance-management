## 1. Investigation and Contract Freeze

- [x] 1.1 Audit existing quant/risk endpoint internals for reusable return-series kernels, timezone normalization seams, and scope validation reuse.
  Notes:
  - Confirm whether existing `scope` + `instrument_symbol` validation helpers can be reused without branching drift.
  - Audit results are locked in `design.md` under `Current-State Audit (Task 1.1)`.
- [x] 1.2 Freeze Monte Carlo parameter envelope (`sims`, horizon, `bust`, `goal`, `seed`) and deterministic defaults for v1.
  Notes:
  - Bounds must protect runtime latency while still enabling useful scenario exploration.
  - Frozen v1 envelope is locked in `design.md` under `Monte Carlo Parameter Envelope Freeze (Task 1.2)`.
- [x] 1.3 Freeze risk-evolution storytelling contract (drawdown path, rolling volatility/beta, return-distribution) and threshold-interpretation copy rules.
  Notes:
  - Keep mixed-unit guardrails explicit and preserve current card-level interpretation contract.
  - Storytelling sequence and interpretation bands are locked in `design.md` under `Risk Storytelling Contract Freeze (Task 1.3)`.
- [x] 1.4 Freeze scope symmetry rules across analytics/risk/simulation/reporting for `portfolio` and `instrument_symbol` contexts.
  Notes:
  - Scope symmetry rules and endpoint targeting are locked in `design.md` under `Scope Symmetry Freeze (Task 1.4)`.

## 2. Fail-First Test Baseline

- [x] 2.1 Add fail-first backend contract tests for Monte Carlo request validation and success payload shape.
- [x] 2.2 Add fail-first backend contract tests for risk-evolution and return-distribution endpoints/payloads.
- [x] 2.3 Add fail-first backend tests for deterministic seed behavior and explicit insufficient-history failures.
  Notes:
  - Include repeated-call assertions for identical input state + seed.
- [x] 2.4 Add fail-first frontend tests for Risk timeline modules (rendering, series toggles, accessibility labels).
- [x] 2.5 Add fail-first frontend tests for Quant/Reports Monte Carlo workflow lifecycle states (`loading`, `error`, `unavailable`, `ready`).
- [x] 2.6 Add fail-first QuantStats adapter compatibility tests for Monte Carlo call paths under pinned runtime.

## 3. Backend Contracts and Service Implementation

- [x] 3.1 Implement typed schemas for Monte Carlo requests/responses and risk-evolution/distribution datasets.
- [x] 3.2 Implement service-layer computations for drawdown path, rolling volatility, rolling beta, and return-distribution buckets.
- [x] 3.3 Implement service-layer Monte Carlo orchestration for `portfolio` and `instrument_symbol` scopes using explicit assumptions metadata.
  Notes:
  - Surface simulation assumptions and caveats in response metadata; do not infer hidden defaults.
- [x] 3.4 Add/extend API routes for risk-evolution and Monte Carlo contracts with fail-fast validation semantics.
- [x] 3.5 Preserve read-only side-effect boundaries and structured logging metadata for new quant/risk execution paths.

## 4. Frontend Risk and Quant/Reports Evolution

- [x] 4.1 Implement Risk route timeline modules for drawdown path and rolling estimators with deterministic legends/toggles.
- [x] 4.2 Implement Risk return-distribution module with explicit bin-policy and interpretation context.
- [x] 4.3 Implement Quant/Reports Monte Carlo control panel (`sims`, horizon, `bust`, `goal`, `seed`) with explicit lifecycle states.
- [x] 4.4 Implement simulation summary cards (percentiles, bust/goal probabilities) and threshold-context explainability affordances.
- [x] 4.5 Ensure keyboard accessibility, responsive behavior, and visual consistency with workspace composition standards.

## 5. Documentation and Governance Updates

- [x] 5.1 Update `docs/guides/frontend-api-and-ux-guide.md` with new risk-evolution and Monte Carlo contracts.
- [x] 5.2 Update `docs/standards/quantstats-standard.md` with simulation parameter policy, interpretation guardrails, and omission semantics.
- [x] 5.3 Update product roadmap/backlog docs to include this phase and explicit non-goal boundaries.
- [x] 5.4 Add `CHANGELOG.md` entry summarizing behavior changes, file touchpoints, and validation evidence.

## 6. Validation and Closeout

- [x] 6.1 Run backend quality gates (`ruff`, `black --check`, `mypy`, `pyright`, `ty`) and targeted portfolio analytics tests.
- [x] 6.2 Run frontend gates (`lint`, `test`, `build`) including new Risk and Quant/Reports suites.
- [x] 6.3 Run OpenSpec validation for the change and all specs; record evidence before handoff/closeout.

## 7. Extension: Profile-Calibrated Monte Carlo Comparison + Portfolio P&L Storytelling

- [x] 7.1 Add fail-first backend tests for profile-scenario matrix outputs (`Conservative`, `Balanced`, `Growth`) from one deterministic simulation context.
  Notes:
  - Assert stable row order and deterministic probability outputs for equivalent input state + seed.
- [x] 7.2 Add backend calibration engine for `monthly` and `annual` basis with explicit sample-size thresholds and fallback metadata.
  Notes:
  - Enforce bounded thresholds and explicit `fallback_reason` when sample size is insufficient.
- [x] 7.3 Extend Monte Carlo response schema/contracts with `profile_scenarios[]` and `calibration_context` while preserving existing manual primary result fields.
- [x] 7.4 Add fail-first frontend tests for panoramic three-scenario comparison readability and interaction controls (`Enable profile compare`, `Calibration basis`, `Apply profile`).
- [x] 7.5 Implement Quant/Reports Monte Carlo UI extension:
  - default-on scenario comparison matrix,
  - side-by-side profile rows for fast interpretation,
  - profile guide module and preset-to-manual copy behavior.
- [x] 7.6 Add/extend analytics contracts and UI copy for portfolio P&L semantics (`realized`, `unrealized`, `period change`, `total return`) with route-level placement consistency (`Home`, `Analytics`, `Quant/Reports`).
  Notes:
  - Keep business statement lines (`COGS`, `OPEX`, `EBITDA`) explicitly out of scope for this dashboard.
- [x] 7.7 Update docs (`frontend-api-and-ux-guide`, `quantstats-standard`, roadmap/backlog) with profile-calibration policy, P&L terminology rules, and UI interpretation guidance.
- [x] 7.8 Run quality gates and OpenSpec validation for the extension scope; record evidence in `CHANGELOG.md`.

## 8. Extension: Portfolio Health Synthesis and KPI Prioritization

- [x] 8.1 Freeze health-synthesis scoring contract in `design.md` (pillars, profile weights, label policy, critical overrides, caveat policy).
  Notes:
  - Keep scoring deterministic and inspectable; no opaque heuristic outputs.
- [x] 8.2 Add fail-first backend contract tests for health-synthesis payload shape (`health_score`, `health_label`, `profile_posture`, `pillars[]`, `key_drivers[]`, `health_caveats[]`).
- [x] 8.3 Add fail-first backend tests for profile posture weighting determinism (`conservative`, `balanced`, `aggressive`) and critical-risk override behavior.
- [x] 8.4 Implement backend health-synthesis schema/service/route contracts in `app/portfolio_analytics` and keep fail-fast semantics for missing prerequisites.
- [x] 8.5 Add fail-first frontend tests for Home health summary module and KPI-priority layering (`Core 10` promoted, advanced metrics secondary).
- [x] 8.6 Implement Home health-at-a-glance module (score/label/profile selector + top drivers + caveats) with deterministic routing to Risk and Quant/Reports details.
- [x] 8.7 Implement Risk + Quant/Reports health-context modules:
  - Risk: risk-pillar contribution context bound to estimator/timeline sections.
  - Quant/Reports: Monte Carlo scenario sensitivity bridge to health interpretation.
- [x] 8.8 Update docs (`frontend-api-and-ux-guide`, `quantstats-standard`, roadmap/backlog) with health-synthesis contract, KPI-priority policy, and interpretation guidance.
- [x] 8.9 Run backend/frontend quality gates and OpenSpec validation for this extension; record evidence in `CHANGELOG.md`.

## 9. Extension: Frontend UI Polish and Table Semantics Hardening

- [x] 9.1 Freeze frontend dense-table semantics and action-density contract in `design.md` (quant lens, contribution table, lifecycle surface, hierarchy controls).
- [x] 9.2 Add fail-first frontend tests for hierarchy default state and sorting affordances.
- [x] 9.3 Implement hierarchy default sector-collapsed behavior and sortable headers with explicit arrow state.
- [x] 9.4 Add fail-first frontend tests for quant lens table semantics and lifecycle compact action grouping.
- [x] 9.5 Implement quant lens table redesign and lifecycle compact action layout polish.
- [x] 9.6 Add fail-first frontend tests for contribution-leaders table readability semantics (`signed contribution`, `net share`, `abs share`).
- [x] 9.7 Implement contribution-leaders table polish and semantic clarity improvements without changing contribution calculations.
- [x] 9.8 Update `frontend-analytics-workspace` delta spec and product/frontend docs with the UI-polish contract.
- [x] 9.9 Run frontend quality gates and OpenSpec validation for extension 9.x; record evidence in `CHANGELOG.md`.
