# QuantStats Standard: Portfolio Analytics Reporting and Adapter Safety

## Overview

This document defines how to use **QuantStats** in this repository for supplemental portfolio analytics, report generation, and Monte Carlo analysis while preserving deterministic and fail-fast contract behavior.

QuantStats is treated as an analytics/reporting adapter layer, not as a replacement for canonical persisted portfolio truth.

## Why QuantStats

- Provides rich portfolio analytics modules (`stats`, `plots`, `reports`).
- Supports HTML tearsheet generation for analyst workflows.
- Includes Monte Carlo utilities for probabilistic path analysis.
- Integrates naturally with pandas return series and existing NumPy/SciPy stack.

## Scope

Applies to:

- supplemental quant metrics exposed by portfolio analytics endpoints
- bounded HTML report generation workflows
- Monte Carlo-based risk exploration modules where explicitly scoped

Does not apply to:

- canonical ledger/accounting truth mutation
- replacing baseline risk estimator contract semantics without approved spec change
- hidden fallback logic that masks adapter incompatibilities

## Installation and Dependency Policy

Use repository-managed dependencies and lockfiles:

```bash
uv add quantstats
```

Notes:

- Keep `quantstats` pinned exactly in `pyproject.toml` and synced in `uv.lock`.
- QuantStats runtime depends on core scientific stack and plotting/reporting packages; maintain lockfile parity to avoid runtime drift.
- QuantStats API compatibility must be treated as version-sensitive and guarded by tests.

## Core Usage Rules

### 1. Treat QuantStats as return-series analytics, not trade-ledger accounting

- QuantStats computes on return periods (daily/weekly/monthly), not discrete trade lifecycle semantics.
- Do not reinterpret period-based metrics as trade-level PnL statistics without explicit translation.
- Keep ledger-native accounting and tax-lot truth in canonical backend slices.

### 2. Use an explicit adapter registry for callable safety

- Map exposed metrics to verified call paths for the pinned QuantStats version.
- Validate adapter call availability in tests before release.
- Do not rely on ad hoc dynamic `getattr` behavior without compatibility checks.

### 2.1 Pinned-version compatibility mapping (`quantstats==0.0.81`)

| Analytics intent | Preferred QuantStats call path | Notes |
| --- | --- | --- |
| Total return | `quantstats.stats.comp` | Return-series input |
| CAGR | `quantstats.stats.cagr` | Annualization assumptions must be explicit |
| Volatility | `quantstats.stats.volatility` | Keep period basis explicit in API metadata |
| Max drawdown | `quantstats.stats.max_drawdown` | Price/return preparation semantics must stay explicit |
| Sharpe | `quantstats.stats.sharpe` | Risk-free and period basis must be explicit |
| Sortino | `quantstats.stats.sortino` | Downside-risk interpretation context required |
| Calmar | `quantstats.stats.calmar` | Depends on drawdown semantics |
| Alpha/Beta | `quantstats.stats.greeks` (`Series['alpha']`, `Series['beta']`) | `stats.alpha`/`stats.beta` are not guaranteed call paths in pinned runtime |

### 3. Handle optional benchmark-relative metrics explicitly

- Benchmark-relative metrics are optional outputs and require compatible benchmark series plus compatible adapter call paths.
- Missing benchmark-compatible calls must be reported explicitly; they must not fabricate values.
- Failures in optional benchmark metrics should not implicitly corrupt core metric outputs.

### 4. Keep report generation bounded and deterministic

- Use explicit report scope (`portfolio`, `instrument_symbol`, or approved ETF scope).
- Validate report parameters and reject unsupported requests explicitly.
- Enforce deterministic report naming/retention and explicit unavailable-state failures for expired artifacts.

### 5. Keep backend report execution non-interactive and server-safe

- For backend workflows, always generate HTML with explicit output path handling.
- Do not rely on notebook/browser-open behavior from QuantStats report APIs.
- Preserve read-only behavior over canonical, ledger, lot, and market-data state while computing reports/metrics.

## Monte Carlo Rules (QuantStats)

QuantStats Monte Carlo uses return shuffling for path analysis:

- Preserves historical return distribution.
- Breaks serial dependency structure by randomizing order.
- Produces path-dependent variability for drawdown and risk characteristics.
- Use explicit simulation parameters (`sims`, `seed`, `bust`, `goal`) and expose assumptions in UI/API metadata.

### Frozen v1 simulation envelope

| Parameter | Bound / rule |
| --- | --- |
| `scope` | `portfolio` or `instrument_symbol` only |
| `instrument_symbol` | required for `instrument_symbol`; omitted for `portfolio` |
| `period` | `30D`, `90D`, `252D`, `MAX` |
| `sims` | `250..5000` |
| `horizon_days` | `5..756` (plus period-aware client caps for `30D/90D/252D`) |
| `seed` | `0..2147483647`, deterministic default when omitted |
| `bust_threshold` | optional, `-0.95..0` |
| `goal_threshold` | optional, `0..3` |
| `calibration_basis` | `monthly`, `annual`, or `manual` |
| `enable_profile_comparison` | boolean toggle for three-profile matrix |
| threshold ordering | when both provided, `bust_threshold < goal_threshold` |

Policy:

- Invalid simulation parameters are explicit `422` client failures.
- Insufficient aligned history is explicit `409`; never fabricate simulation output.
- Equivalent persisted input state + seed must remain deterministic.
- Profile comparison mode evaluates one deterministic path set and derives three profile outcomes (`Conservative`, `Balanced`, `Growth`) from that shared simulation context.
- Historical calibration (`monthly`/`annual`) must expose sample-size and fallback metadata; insufficient sample must be explicit, not silent.

Important interpretation note:

- QuantStats documentation states shuffled-path simulations preserve the compounded terminal product; path-dependent metrics vary by sequence even when terminal product is preserved.

## Frontend Integration Rules

- Home route is an executive snapshot surface; it links to Quant/Reports and does not own report generation controls.
- Risk route remains the primary context for interpretation-sensitive risk metrics (drawdown, volatility, beta, downside deviation, VaR, expected shortfall, methodology labels).
- Quant/Reports route must display explicit scope, provenance, and generation lifecycle status (`loading`, `error`, `unavailable`, `ready`).
- All quant-derived values must preserve deterministic formatting semantics (decimal-safe money/ratio presentation).
- Non-functional analytical actions are prohibited; workflow actions must live in stable, testable surfaces (not tooltip-only controls).
- KPI copy must keep portfolio-investing semantics (`realized/unrealized/period P&L`, `total return`) and must not mix business statement lines (`COGS`, `OPEX`, `EBITDA`).

### Metric Placement Matrix

| Surface | Primary metric scope | Rules |
| --- | --- | --- |
| Home | High-signal KPI snapshot | No report generation controls; provide deterministic deep-link to Quant/Reports |
| Risk | Interpretation-sensitive risk metrics | Drawdown/volatility/beta/downside deviation/VaR/expected shortfall and methodology metadata are first-class here |
| Quant/Reports | Expanded quant diagnostics and tearsheets | Explicit report scope, benchmark context, generation lifecycle state, and artifact preview |

### Risk interpretation guardrails

Risk modules must keep mixed-unit and threshold-context guardrails explicit:

- Mixed-unit estimator payloads must render separated groups (`percent` vs `ratio`) and must not be merged into a single misleading axis.
- Each promoted estimator should expose threshold-context guidance:
  - `max_drawdown`: favorable `<=10%`, caution `>10% and <=20%`, elevated `>20%`
  - `volatility_annualized`: favorable `<=15%`, caution `>15% and <=25%`, elevated `>25%`
  - `beta`: favorable `0.8..1.2`, caution `0.6..0.8 or 1.2..1.4`, elevated `<0.6 or >1.4`
  - `value_at_risk_95`: favorable `<=2%`, caution `>2% and <=5%`, elevated `>5%`
  - `expected_shortfall_95`: favorable `<=3%`, caution `>3% and <=6%`, elevated `>6%`

### Simulation-context omission semantics

Quant report contracts must not imply simulation readiness by absence:

- `simulation_context_status=ready`: simulation metadata was computed and is safe to interpret.
- `simulation_context_status=unavailable`: report generation succeeded but simulation context is intentionally omitted with factual reason.
- `simulation_context_status=error`: simulation context failed; lifecycle is explicit and separate from core report artifact availability.

## Derived Metrics Scope Boundaries

Shipped in Phase F:

- Quant scorecards with benchmark omission context
- Report lifecycle + artifact preview
- Monthly returns heatmap-style module with precision caveat copy

Shipped in Phase G:

- risk-evolution modules (drawdown path + rolling volatility/beta timelines)
- deterministic return-distribution histogram modules
- bounded Monte Carlo control workflow and simulation summary cards
- profile-calibrated three-scenario Monte Carlo comparison with basis controls (`monthly`, `annual`, `manual`)

## Testing Rules

- Add fail-first tests for QuantStats adapter callable compatibility.
- Add backend tests for report generation success, validation failure, and artifact lifecycle failure.
- Add frontend tests for section-scoped Home error behavior and quant/report action flows.
- Add regression fixtures for selected quant metrics to detect version drift after dependency updates.

## Validation Commands

QuantStats integration quality is validated through repository gates:

```bash
uv run pytest -v app/portfolio_analytics/tests
uv run mypy app/
uv run pyright app/
uv run ty check app
npm --prefix frontend run test
npm --prefix frontend run build
```

## Resources (Official QuantStats)

- Repository: https://github.com/ranaroussi/quantstats
- Docs directory: https://github.com/ranaroussi/quantstats/tree/main/docs
- Monte Carlo docs: https://github.com/ranaroussi/quantstats/blob/main/docs/montecarlo.md
- README (modules, report APIs, usage notes): https://github.com/ranaroussi/quantstats
- Example tearsheet HTML: https://rawcdn.githack.com/ranaroussi/quantstats/main/docs/tearsheet.html

---

**Last Updated:** 2026-03-30
