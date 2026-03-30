## Context

Phase F delivered a professional route structure (`Home`, `Analytics`, `Risk`, `Quant/Reports`) plus explainability and report lifecycle states. The remaining gap is analytical depth: users can interpret current values, but they still lack trajectory and scenario context for long-term investing decisions.

Current standards already approve these follow-ups:

- drawdown path visualization
- rolling volatility/beta timelines
- return-distribution histogram
- QuantStats Monte Carlo exploration with explicit assumptions

This phase operationalizes those approved follow-ups while preserving repository constraints: strict typing, fail-fast contracts, deterministic outputs, and route-scoped analytical storytelling.

## Current-State Audit (Task 1.1)

### Reusable backend kernels confirmed

- `normalize_chart_scope()` already enforces canonical scope semantics (`portfolio` vs `instrument_symbol`) with explicit client-facing failures.
- `_load_open_position_price_inputs()` is already a shared read-only ingestion seam for time-series, risk estimators, quant metrics, and quant report generation.
- `_select_aligned_timestamps()` + `_build_aligned_price_frame()` provide deterministic aligned-price preprocessing with explicit missing-data and ordering failures.
- `_build_returns_series_from_values()` and `_build_portfolio_returns_series()` already enforce finite-value and positive-value fail-fast behavior for return-series math.
- `_normalize_quantstats_report_inputs()` + `_normalize_quantstats_report_series_index()` already normalize report inputs for QuantStats HTML compatibility (UTC-naive DatetimeIndex).

### Scope-validation and timezone seams already in production

- Time-series endpoint already supports `scope` + `instrument_symbol` with normalized symbol handling.
- Quant-report request normalization already enforces equivalent scope rules in request body form.
- Price-history timestamps are coerced to UTC via `_coerce_price_row_timestamp()` and validated for strict UTC ordering via `_validate_aligned_timestamp_index()`.

### Current gaps this phase must close

- No Monte Carlo API/service contract currently exists.
- Risk-estimator route currently supports only `window_days`, without symbol-scoped risk execution.
- Risk UI currently renders unit-split range tracks and metric ledger but not timeline modules or return distribution.
- Quant/Reports UI currently lacks simulation controls and simulation lifecycle context.

## Monte Carlo Parameter Envelope Freeze (Task 1.2)

The v1 simulation envelope is frozen as:

| Field | Policy |
|---|---|
| `scope` | `portfolio` or `instrument_symbol` only |
| `instrument_symbol` | required for `instrument_symbol` scope; forbidden for `portfolio` scope |
| `period` | existing period enum (`30D`, `90D`, `252D`, `MAX`) |
| `sims` | integer, bounded `250..5000`, default `1000` |
| `horizon_days` | integer, bounded `5..756`, with period-aware caps (`30D<=29`, `90D<=89`, `252D<=251`, `MAX<=756`) and defaults (`20`,`60`,`126`,`252`) |
| `bust_threshold` | optional simple-return threshold, bounded `[-0.95, 0.0]` |
| `goal_threshold` | optional simple-return threshold, bounded `[0.0, 3.0]` |
| `seed` | optional integer, bounded `[0, 2_147_483_647]`; deterministic default `20260330` |

Contract rules:

- Requests violating bounds fail explicitly with `422`.
- `bust_threshold` and `goal_threshold` are optional independently, but when both are provided, `bust_threshold < goal_threshold` is required.
- Responses must echo effective simulation parameters so repeated calls can be reproduced.

### Extension: Profile-Calibrated Scenario Matrix (Task 1.5)

This extension adds a deterministic "compare 3 levels" workflow without removing manual parameter control:

- Levels: `Conservative`, `Balanced`, `Growth`.
- Each level defines one `bust_threshold` and one `goal_threshold`.
- All levels are evaluated against the same simulation run context (same `scope`, period, horizon, seed, and simulation paths).

Calibration modes:

| Mode | Source series | Use case |
|---|---|---|
| `monthly` (default) | persisted monthly compounded returns derived from scoped value series | stable long-term baseline with enough observations |
| `annual` | persisted annual compounded returns derived from scoped value series | strategic long-horizon sanity checks when multi-year history is present |
| `manual` | user-specified thresholds only | fully custom exploration |

Why monthly default:

- Annual samples are often too sparse for robust percentile calibration in personal portfolios.
- Monthly basis gives a better balance between noise reduction and sample size.

Calibrated profile thresholds are deterministic and bounded:

- `bust_threshold` levels are derived from lower-tail realized-return quantiles and clamped to API bounds.
- `goal_threshold` levels are derived from central/upper realized-return quantiles and clamped to API bounds.
- If historical sample is insufficient, the service returns explicit fallback metadata and uses fixed guardrail defaults.

Output contract for extension:

- `profile_scenarios[]`: per-profile thresholds + `bust_probability` + `goal_probability` + interpretation label.
- `calibration_context`: basis (`monthly|annual|manual`), sample size, lookback span, fallback reason (nullable).
- `manual_primary_result`: existing single-scenario output remains first-class for backwards compatibility.

Default execution behavior:

- The Monte Carlo module executes with profile comparison enabled by default.
- One run produces:
  - the existing manual primary result (current bust/goal inputs),
  - and a three-row profile comparison matrix (`Conservative`, `Balanced`, `Growth`) using the selected calibration basis.
- Users can disable profile comparison without losing manual simulation controls.

Deterministic profile calibration policy:

- Calibration is computed from the same scoped return series already used by simulation.
- `monthly` basis:
  - aggregate returns to month-end compounded returns.
  - minimum sample target: 24 monthly observations; otherwise explicit fallback metadata is emitted.
- `annual` basis:
  - aggregate returns to year-end compounded returns.
  - minimum sample target: 5 annual observations; otherwise explicit fallback metadata is emitted.
- Fallback path:
  - uses fixed profile thresholds from contract defaults;
  - includes `fallback_reason` and `effective_basis` in response metadata.

Profile threshold derivation (frozen for v1 extension):

- `Conservative`: tighter loss tolerance and lower goal barrier (more capital-preservation posture).
- `Balanced`: median baseline thresholds.
- `Growth`: wider drawdown tolerance and higher goal barrier.
- Exact quantile-to-threshold mapping is deterministic and versioned in service metadata to avoid hidden heuristic drift.

Frontend control contract for this extension:

- `Enable profile compare` toggle (default: on).
- `Calibration basis` segmented selector (`monthly` / `annual` / `manual`).
- `Apply profile` quick-action controls (`Conservative`, `Balanced`, `Growth`) that copy profile thresholds into manual inputs for "what-if" iteration.
- `Profile guide` panel with concise interpretation guidance and recommended starting ranges per investor posture.

Scenario-comparison visualization contract:

- Primary visualization is a three-row comparison matrix with fixed row order (`Conservative`, `Balanced`, `Growth`).
- Each row must show, in one scan line: thresholds, bust probability, goal probability, and a qualitative signal.
- Secondary detail (percentile cards/envelope) remains available below the matrix for deeper inspection.
- Sorting and hidden auto-reordering are forbidden; the profile rows remain stable to preserve pattern memory.

### P&L Framing for Portfolio Context (Task 1.6)

Portfolio P&L semantics in this product are investment-focused, not business-income-statement focused.

In-scope portfolio P&L concepts:

- `unrealized_pnl`: mark-to-market gain/loss on open positions.
- `realized_pnl`: locked gain/loss from closed lots/events.
- `period_pnl`: change over selected period (`30D/90D/252D/MAX` as applicable).
- `total_return`: compounded return context for benchmark-relative interpretation.

Out-of-scope business statement concepts for this slice:

- `COGS`, `OPEX`, `EBITDA`, and full operating income statement lines.
- Rationale: these belong to company financial statement analysis, not portfolio performance decomposition from user-held positions.

Route-level placement guidance for P&L storytelling:

- `Home` (executive snapshot): concise current `unrealized_pnl`, period change, and quick benchmark-relative context.
- `Analytics` (decomposition): symbol and component attribution (realized, unrealized, dividend, reconciliation) with trend context.
- `Quant/Reports` (forward-looking): Monte Carlo scenario comparison and profile-guided bust/goal probability interpretation.

### Portfolio Health Synthesis Contract Freeze (Task 8.1)

Current modules expose many valid KPIs, but users still need to manually stitch them into one decision posture.
This extension adds a deterministic synthesis layer that answers "how healthy is this portfolio for my risk profile?" without hiding underlying metrics.

Health synthesis outputs (contract-level):

- `health_label`: one of `healthy`, `watchlist`, `stressed`.
- `health_score`: bounded score `0..100`.
- `profile_posture`: `conservative`, `balanced`, or `aggressive`.
- `pillars[]`: fixed four-pillars list with per-pillar score and supporting KPIs:
  - `growth`
  - `risk`
  - `risk_adjusted_quality`
  - `resilience`
- `key_drivers[]`: top positive and top negative contributors with deterministic ordering and factual rationale text.
- `health_caveats[]`: explicit caveats for missing benchmark context, insufficient history, or partial metric availability.

Pillar KPI mapping (frozen for v1 extension):

| Pillar | Primary KPIs |
|---|---|
| `growth` | `cagr`, `cumulative_return`, `1y_return`, `3y_annualized_return` |
| `risk` | `max_drawdown`, `volatility_annualized`, `expected_shortfall_95`, `value_at_risk_95` |
| `risk_adjusted_quality` | `sharpe_ratio`, `sortino_ratio`, `calmar_ratio` |
| `resilience` | `recovery_factor`, `longest_drawdown_days`, `win_month` |

Profile posture weighting (frozen defaults):

| Profile | Growth | Risk | Risk-adjusted quality | Resilience |
|---|---:|---:|---:|---:|
| `conservative` | 20% | 40% | 25% | 15% |
| `balanced` | 30% | 30% | 25% | 15% |
| `aggressive` | 35% | 20% | 30% | 15% |

Health label policy (frozen defaults):

- `healthy`: score `>= 70` and no critical risk override.
- `watchlist`: score `45..69` or one critical risk override.
- `stressed`: score `< 45` or two-or-more critical risk overrides.

Critical risk overrides (v1):

- `max_drawdown` absolute value `> 30%`.
- `expected_shortfall_95` absolute value `> 6%`.
- `calmar_ratio < 0.3` when sufficient history is available.

UX storytelling posture for synthesis:

- `Home`: one compact health panel with score/label, profile selector, and top 3 drivers.
- `Risk`: displays "risk pillar contribution" and deep-links into drawdown/volatility/tail metrics.
- `Quant/Reports`: displays scenario sensitivity note tying Monte Carlo profile outcomes to health posture.

Interpretation constraints:

- This is an interpretation aid, not financial advice.
- Core 10 KPIs are promoted first; advanced KPIs remain accessible but visually secondary.
- Health output must expose exact metric contributions and thresholds (no opaque scoring).

## Risk Storytelling Contract Freeze (Task 1.3)

Risk route narrative sequence is frozen to:

1. bounded estimator cards/range tracks (current-state snapshot),
2. drawdown path timeline,
3. rolling estimator timelines (volatility, beta),
4. return-distribution histogram with deterministic bin policy.

Interpretation-band copy is frozen as:

| Metric | Favorable | Caution | Elevated risk |
|---|---|---|---|
| `max_drawdown` (absolute) | `<= 10%` | `> 10% and <= 20%` | `> 20%` |
| `volatility_annualized` | `<= 15%` | `> 15% and <= 25%` | `> 25%` |
| `beta` | `0.8-1.2` market-like | `0.6-0.8` or `1.2-1.4` | `< 0.6` or `> 1.4` |
| `value_at_risk_95` (absolute) | `<= 2%` | `> 2% and <= 5%` | `> 5%` |
| `expected_shortfall_95` (absolute) | `<= 3%` | `> 3% and <= 6%` | `> 6%` |

These bands are interpretation guidance only and must always be shown with methodology context and selected window.

## Scope Symmetry Freeze (Task 1.4)

Scope behavior is frozen across relevant analytics/risk/simulation/report contracts:

- `scope=portfolio`: `instrument_symbol` must be omitted.
- `scope=instrument_symbol`: non-empty `instrument_symbol` is required and normalized (`trim + uppercase`).
- Scope validation errors are explicit client-facing failures; no implicit scope coercion.

Symmetry targets by surface:

- Existing: `/time-series` (query-contract scope), `/quant-reports` (body-contract scope).
- Phase G additions: risk-evolution dataset endpoints and Monte Carlo endpoints must use the same semantics.
- Risk estimator route extension in this phase must align with the same scope posture to avoid split behavior between Risk and Quant/Reports workflows.

## Extension 9: Frontend UI Polish and Table Semantics Hardening

This extension addresses professional-readability gaps observed in dense analytical modules while preserving route contracts and analytical formulas.

Frozen UX polish contract:

- Quant lens (`30D/90D/252D`) must render with deterministic column alignment, tabular numeric rhythm, and stable header semantics.
- Quant report lifecycle action surface must prioritize scope + primary CTA + lifecycle state in one compact control cluster.
- Contribution leaders tables must expose directional and concentration context with unambiguous labels (`signed contribution`, `net share`, `abs share`).
- Portfolio hierarchy must load with sector groups collapsed by default and provide explicit sortable-header affordances with visible arrow state.

Non-functional constraints:

- No backend analytics formula changes.
- No scope/period contract drift.
- No stack migration; polish is implemented within current frontend architecture and style system.

## Goals / Non-Goals

**Goals:**
- Add deterministic Monte Carlo simulation support for `portfolio` and `instrument_symbol` scopes.
- Add risk-evolution datasets (drawdown path, rolling vol/beta, return distribution) for chart-ready frontend rendering.
- Upgrade Risk route with timeline and distribution storytelling that complements existing estimator cards.
- Upgrade Quant/Reports with simulation-aware diagnostics and artifact lifecycle context.
- Keep all quant/risk outputs explainable with explicit assumptions, methodology metadata, and threshold interpretation context.
- Add deterministic portfolio-health synthesis outputs and route-level interpretation modules that reduce KPI overload for non-expert users.

**Non-Goals:**
- Replacing the pinned QuantStats dependency.
- Introducing trade execution, optimization, or allocation recommendation engines.
- Turning simulation output into financial advice or prescriptive portfolio actions.
- Expanding into authentication, cloud deployment, or scheduler infrastructure.

## Decisions

### Decision 1: Expose Monte Carlo as explicit backend contract, not frontend-local computation
- Decision: Monte Carlo simulation is computed server-side and exposed by portfolio analytics contracts with explicit scope and parameter metadata.
- Rationale: preserves deterministic behavior, fail-fast validation, and testability; avoids client-side numerical drift.
- Alternatives considered:
  - frontend-only simulation: rejected due non-determinism and weak auditability.
  - offline-only report embedding: rejected because users need interactive scenario tuning.

### Decision 2: Freeze simulation parameter envelope and seed policy
- Decision: enforce bounded parameters (`sims`, horizon, `bust`, `goal`) and deterministic seeding policy (`seed` explicit or server default with explicit metadata echo).
- Rationale: prevents hidden variability and protects performance.
- Alternatives considered:
  - unbounded simulation counts: rejected due runtime risk.
  - implicit random seed without reporting: rejected due non-reproducibility.

### Decision 3: Keep risk visualization split by semantic purpose
- Decision: Risk route will keep existing guardrailed cards, then add separate modules for timelines and distributions (not one overloaded chart).
- Rationale: mixed-units and mixed-semantics visuals reduce interpretability.
- Alternatives considered:
  - one all-in-one composite chart: rejected due readability and accessibility costs.

### Decision 4: Add simulation awareness to Quant/Reports lifecycle
- Decision: report lifecycle metadata explicitly communicates whether simulation context is available, omitted, or failed.
- Rationale: avoids silent degradation in report interpretation.
- Alternatives considered:
  - implicit omission in HTML only: rejected by explicit-state policy.

### Decision 5: Keep scope symmetry across analytics, risk, and simulation modules
- Decision: `scope={portfolio|instrument_symbol}` and `instrument_symbol` requirements must remain consistent across new risk/simulation contracts.
- Rationale: predictable UX and deterministic API behavior.
- Alternatives considered:
  - simulation only at portfolio level: rejected because instrument-level diagnosis is a stated product need.

### Decision 6: Evaluate profile scenarios from one simulation context, not three independent runs
- Decision: profile comparison computes one deterministic simulation path set and derives probabilities for all profile threshold pairs from that shared path set.
- Rationale: keeps UX fast, preserves apples-to-apples comparison, and avoids tripling runtime cost.
- Alternatives considered:
  - three independent Monte Carlo runs: rejected due latency and inconsistent random path comparability.

### Decision 7: Calibrate defaults from realized returns with explicit basis metadata
- Decision: support `monthly` and `annual` calibration basis, defaulting to `monthly`, and always echo calibration metadata and fallback reason.
- Rationale: prevents hidden heuristics and teaches users why defaults look the way they do.
- Alternatives considered:
  - hardcoded profile defaults only: rejected because user requested historical realism.
  - annual-only calibration: rejected because sample size is too small in many portfolios.

### Decision 8: Keep portfolio P&L semantics separate from company income-statement semantics
- Decision: product contracts use investment P&L terms (realized/unrealized/period/total return) and explicitly avoid introducing business statement lines (`COGS`, `OPEX`, `EBITDA`) in this slice.
- Rationale: prevents conceptual drift and keeps dashboard interpretation aligned with user-held portfolio data.
- Alternatives considered:
  - blending company-statement and portfolio P&L terms in one KPI layer: rejected due semantic confusion and low actionability for this route set.

### Decision 9: Add deterministic health synthesis instead of heuristic-only narrative copy
- Decision: health interpretation is produced from explicit weighted pillars and threshold rules, not free-form narrative generation.
- Rationale: keeps interpretation reproducible, testable, and auditable across scopes and periods.

### Decision 10: Apply template-inspired UI consistency patterns without framework adoption
- Decision: reuse stable patterns (UI primitive consistency, compact lifecycle states, predictable table semantics) discovered in reference template analysis, without adopting template framework/runtime choices.
- Rationale: capture readability and interaction gains while preserving current repository architecture and delivery velocity.
- Alternatives considered:
  - copy-only manual interpretation blocks: rejected due inconsistency and low personalization.
  - opaque model-based health scoring: rejected due explainability and governance constraints.

## Risks / Trade-offs

- [Risk] Monte Carlo can be interpreted as forecasting certainty.
  Mitigation: require assumption and caveat copy in API/UX contracts (`shuffled returns`, `not predictive`, `scenario-based`).

- [Risk] Runtime cost may degrade responsiveness.
  Mitigation: cap `sims` and horizon ranges; add response timing telemetry and fail-fast validation for expensive requests.

- [Risk] Additional charts can increase cognitive load.
  Mitigation: sequence visuals with route storytelling (cards -> timelines -> distribution -> simulation), plus concise explainability popovers.

- [Risk] Benchmark alignment gaps may produce partial outputs.
  Mitigation: keep omission metadata explicit; do not fabricate benchmark-relative series.

- [Risk] Single health score may hide nuance and encourage overconfidence.
  Mitigation: require pillar breakout, driver list, and caveats alongside any aggregate label.

## Migration Plan

1. Lock OpenSpec contracts (proposal/design/specs/tasks) for simulation and risk-evolution behavior.
2. Add fail-first backend/frontend tests for missing contracts, invalid params, and new UX modules.
3. Implement backend schemas/services/routes for simulation + risk-evolution datasets.
4. Implement frontend Risk and Quant/Reports module upgrades with explainability and lifecycle states.
5. Implement health synthesis contract + Home/Risk/Quant interpretation modules with profile posture support.
6. Update docs/standards/changelog with methodology and validation evidence.
7. Validate with backend/frontend/OpenSpec gates and targeted integration suites.

Rollback strategy:
- Disable new simulation and risk-evolution modules behind route-level fallbacks while retaining existing Phase F cards and report lifecycle behavior.

## Open Questions

None.
