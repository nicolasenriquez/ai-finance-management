# Portfolio KPI Governance Catalog

## Purpose
Define one deterministic KPI governance contract for the portfolio workspace so promoted
metrics keep stable interpretation tiering, route ownership, decision relevance, and copy
semantics.

## Route Labels
| Route key | User-facing label | Interpretation job |
| --- | --- | --- |
| `home` | Portfolio command home | Portfolio operating posture and first-pass interpretation. |
| `analytics` | Performance and contribution analytics | Attribution concentration and allocation drift interpretation. |
| `risk` | Bounded estimator workspace | Risk posture interpretation with unit-aware estimator guardrails. |
| `reports` | Quant diagnostics and report lifecycle | Goal progress and forecast-confidence interpretation before advanced diagnostics. |

## Promoted KPI Catalog
| Metric ID | Tier | Route owner | Decision tags | Plain-language interpretation |
| --- | --- | --- | --- | --- |
| `market_value_usd` | `core_10` | `home` | `allocation_review` | Current portfolio scale and open-position exposure. |
| `unrealized_gain_pct` | `core_10` | `home` | `allocation_review`, `risk_posture` | Open-position posture versus cost basis. |
| `realized_gain_usd` | `core_10` | `home` | `goal_progress` | Locked gains/losses relevant for goal tracking. |
| `dividend_net_usd` | `core_10` | `home` | `income_monitoring` | Net dividend income contribution. |
| `top_contribution_concentration_pct` | `core_10` | `analytics` | `allocation_review`, `risk_posture` | How concentrated period impact is in top movers. |
| `max_drawdown_pct` | `core_10` | `risk` | `risk_posture` | Peak-to-trough stress magnitude for selected window. |
| `volatility_annualized_pct` | `core_10` | `risk` | `risk_posture` | Realized dispersion and risk-budget pressure. |
| `beta_ratio` | `core_10` | `risk` | `risk_posture` | Market sensitivity versus benchmark context. |
| `goal_hit_probability_pct` | `core_10` | `reports` | `goal_progress` | Probability of reaching configured target threshold. |
| `forecast_confidence_pct` | `core_10` | `reports` | `forecast_interpretation` | Confidence quality for promoted forecast outputs. |
| `sharpe_ratio` | `advanced` | `reports` | `risk_posture` | Risk-adjusted excess return efficiency relative to realized volatility. |
| `sortino_ratio` | `advanced` | `reports` | `risk_posture` | Downside-risk-adjusted return quality for asymmetric risk review. |
| `value_at_risk_95` | `advanced` | `risk` | `risk_posture` | Estimated one-tail loss threshold under selected confidence policy. |
| `expected_shortfall_95` | `advanced` | `risk` | `risk_posture` | Average loss when outcomes breach the 95% VaR threshold. |

## Explainability Copy Rules
- Promoted KPI labels must stay in portfolio and personal-finance vocabulary.
- `core_10` cards lead with decision relevance before advanced math context.
- Advanced metrics remain available but must not displace first-viewport interpretation copy.
- Every promoted KPI entry must keep one plain-language interpretation sentence.
