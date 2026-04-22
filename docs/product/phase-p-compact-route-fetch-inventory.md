# Phase P Compact Route Fetch Inventory

Change: `phase-p-dashboard-saas-hardening-before-dca`
Date: `2026-04-18`

## Scope

First-surface modules for:
- `/portfolio/home`
- `/portfolio/analytics`
- `/portfolio/risk`
- `/portfolio/signals` (visible label: `Opportunities`)

Classification legend:
- `contract-backed`: rendered directly from typed backend payloads
- `derived`: deterministic frontend computation from contract-backed payloads
- `pseudo/static`: fixed constants or placeholder-like rendering not tied to live contracts

## Current State Inventory (Pre-Refactor)

| Route | Module | Current data owner | Classification | Notes |
| --- | --- | --- | --- | --- |
| `/portfolio/home` | KPI strip | `summary + command-center` hooks | `derived` | Deterministic aggregation from contracts. |
| `/portfolio/home` | Equity curve vs benchmark | `topMovers` derived rows | `pseudo/static` | Visual is list-based placeholder, not real chart module. |
| `/portfolio/home` | Attention panel | `command-center` insights + summary | `derived` | Contract-backed inputs but list UI only. |
| `/portfolio/home` | Allocation snapshot | `hierarchy` | `derived` | Deterministic weights from groups. |
| `/portfolio/home` | Top movers table | `summary` | `contract-backed` | Uses live holdings rows. |
| `/portfolio/home` | Holdings summary table | `summary` | `contract-backed` | Uses live holdings rows. |
| `/portfolio/analytics` | Performance curve | route constant `PERFORMANCE_CURVE_POINTS` | `pseudo/static` | Not linked to live time-series contract. |
| `/portfolio/analytics` | Attribution waterfall | route constant `ATTRIBUTION_WATERFALL_STEPS` | `pseudo/static` | Not linked to contribution decomposition contract. |
| `/portfolio/analytics` | Contribution leaders table | `contribution + summary + hierarchy` | `contract-backed` | Live symbols and contribution values. |
| `/portfolio/analytics` | Monthly heatmap | route constant `MONTHLY_HEATMAP` | `pseudo/static` | Placeholder values. |
| `/portfolio/analytics` | Rolling return table | route constant `ROLLING_RETURN_WINDOWS` | `pseudo/static` | Placeholder values. |
| `/portfolio/risk` | Risk posture | route constant `RISK_METRICS` | `pseudo/static` | Not linked to live risk estimator contracts. |
| `/portfolio/risk` | Drawdown timeline | route constant `DRAWDOWN_TIMELINE` | `pseudo/static` | Placeholder values. |
| `/portfolio/risk` | Return distribution | route constant `RETURN_DISTRIBUTION` | `pseudo/static` | Placeholder values. |
| `/portfolio/risk` | Risk/return scatter | route constant `RISK_RETURN_SCATTER` | `pseudo/static` | Placeholder values. |
| `/portfolio/risk` | Correlation heatmap | route constant `CORRELATION_ROWS` | `pseudo/static` | Placeholder values. |
| `/portfolio/risk` | Concentration table | `summary + command-center` | `derived` | Partially contract-backed. |
| `/portfolio/signals` | Trend regime summary | route constant `TREND_REGIME_SUMMARY` | `pseudo/static` | Static rows. |
| `/portfolio/signals` | Momentum ranking | `summary` | `derived` | Deterministic score from live unrealized pct. |
| `/portfolio/signals` | Technical signals table | `summary + feature flags` | `derived` | Deterministic rows from live holdings plus gates. |
| `/portfolio/signals` | Watchlist panel | `summary + hierarchy` | `derived` | Deterministic selection from live holdings. |

## Target Ownership After Stage 2 and Stage 3

| Route | Target owner | Expected first-surface behavior |
| --- | --- | --- |
| `/portfolio/home` | Route-level TanStack query orchestration | Parallel first-surface loading (`summary`, `command-center`, `hierarchy`, `time-series`) with contract-backed Recharts hero chart. |
| `/portfolio/analytics` | Route-level TanStack query orchestration | Parallel first-surface loading with contract-backed performance/ranking/waterfall charts. |
| `/portfolio/risk` | Route-level TanStack query orchestration | Parallel first-surface loading with contract-backed drawdown/rolling/distribution charts. |
| `/portfolio/signals` | Route-level TanStack query orchestration | Parallel first-surface loading with deterministic tactical derivation and factual async-state copy. |

## Refactor Guardrails

- Preserve `/portfolio/signals` slug and `Opportunities` visible label.
- Keep tactical modules secondary relative to home/risk narrative.
- Keep module-level failure isolation and explicit retry surfaces.
- Avoid backend contract invention in Phase P.
