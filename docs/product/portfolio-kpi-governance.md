# Portfolio KPI And Widget Governance Catalog

## Purpose
Define one deterministic governance contract for promoted KPI and widget surfaces so interpretation tiering, route ownership, question-to-decision mapping, and comparison framing remain stable.

## Route Labels
| Route key | User-facing label | Lens | Interpretation job |
| --- | --- | --- | --- |
| `dashboard` | Overview command home | `Overview` | Portfolio operating posture and highlights-first interpretation. |
| `holdings` | Holdings explorer | `Holdings` | Position, lot, and concentration interpretation by instrument. |
| `performance` | Performance and contribution analytics | `Performance` | Attribution concentration and period-impact interpretation. |
| `risk` | Bounded estimator workspace | `Risk` | Downside and estimator posture interpretation with unit guardrails. |
| `rebalancing` | Rebalancing and quant diagnostics | `Rebalancing` | Scenario comparison, optimization context, and forecast interpretation. |
| `copilot` | Portfolio copilot | `Copilot` | Grounded narrative explanation with evidence-linked follow-ups. |
| `transactions` | Cash and ledger operating narrative | `Cash/Transactions` | Deterministic cash-event and ledger-flow interpretation. |

Legacy compatibility aliases remain supported for route migration:
`home -> dashboard`, `analytics -> performance`, `reports -> rebalancing`.

## Promoted KPI Catalog
| Metric ID | Tier | Route owner | Question owner | Decision tags | Comparison framing | Plain-language interpretation |
| --- | --- | --- | --- | --- | --- | --- |
| `market_value_usd` | `core_10` | `dashboard` | Portfolio operating posture | `allocation_review` | Current period vs prior period value | Current portfolio scale and open-position exposure. |
| `unrealized_gain_pct` | `core_10` | `dashboard` | Portfolio operating posture | `allocation_review`, `risk_posture` | Gain/loss versus cost basis | Open-position posture versus cost basis. |
| `realized_gain_usd` | `core_10` | `dashboard` | Portfolio operating posture | `goal_progress` | Realized gains versus period bridge | Locked gains/losses relevant for goal tracking. |
| `dividend_net_usd` | `core_10` | `dashboard` | Portfolio operating posture | `income_monitoring` | Dividend contribution versus total period move | Net dividend income contribution. |
| `top_contribution_concentration_pct` | `core_10` | `performance` | Attribution concentration interpretation | `allocation_review`, `risk_posture` | Top symbol absolute share versus total absolute contribution | How concentrated period impact is in top movers. |
| `max_drawdown_pct` | `core_10` | `risk` | Risk posture interpretation | `risk_posture` | Current drawdown versus worst historical path | Peak-to-trough stress magnitude for selected window. |
| `volatility_annualized_pct` | `core_10` | `risk` | Risk posture interpretation | `risk_posture` | Current period versus prior rolling volatility | Realized dispersion and risk-budget pressure. |
| `beta_ratio` | `core_10` | `risk` | Risk posture interpretation | `risk_posture` | Beta versus benchmark sensitivity baseline (`1.0`) | Market sensitivity versus benchmark context. |
| `goal_hit_probability_pct` | `core_10` | `rebalancing` | Goal progress and confidence interpretation | `goal_progress` | Goal probability versus bust probability | Probability of reaching configured target threshold. |
| `forecast_confidence_pct` | `core_10` | `rebalancing` | Goal progress and confidence interpretation | `forecast_interpretation` | Forecast confidence versus lifecycle readiness state | Confidence quality for promoted forecast outputs. |
| `sharpe_ratio` | `advanced` | `rebalancing` | Advanced diagnostics | `risk_posture` | Sharpe versus period peers | Risk-adjusted excess return efficiency relative to realized volatility. |
| `sortino_ratio` | `advanced` | `rebalancing` | Advanced diagnostics | `risk_posture` | Sortino versus downside-risk peers | Downside-risk-adjusted return quality for asymmetric risk review. |
| `value_at_risk_95` | `advanced` | `risk` | Advanced diagnostics | `risk_posture` | VaR versus expected shortfall | Estimated one-tail loss threshold under selected confidence policy. |
| `expected_shortfall_95` | `advanced` | `risk` | Advanced diagnostics | `risk_posture` | Expected shortfall versus VaR gap | Average loss when outcomes breach the 95% VaR threshold. |

## Widget Governance Decisions
| Widget ID | Disposition | Severity | Rationale | Destination behavior |
| --- | --- | --- | --- | --- |
| `analytics-contribution-waterfall` | `MOVE` | Medium | Duplicates primary contribution question in first surface. | Hidden behind advanced attribution disclosure. |
| `risk-rolling-estimator` | `MOVE` | High | Useful but secondary for first-pass risk posture triage. | Hidden behind advanced risk disclosure. |
| `risk-correlation-network` | `MOVE` | High | High cognitive load for first-pass interpretation. | Hidden behind advanced risk disclosure. |
| `risk-tail-diagnostics` | `MOVE` | High | Secondary to estimator + drawdown + distribution baseline. | Hidden behind advanced risk disclosure. |
| `reports-advanced-risk-lab` | `MOVE` | High | Advanced optimization analysis should not compete with lifecycle and Monte Carlo first view. | Hidden behind advanced reports disclosure. |
| `reports-ml-insights` | `MOVE` | High | Governance-heavy diagnostics are advanced interpretation. | Hidden behind advanced reports disclosure. |
| `reports-health-bridge` | `MOVE` | Medium | Useful cross-check but non-primary for first report decision. | Hidden behind advanced reports disclosure. |

## Explainability Copy Rules
- Promoted KPI labels must stay in portfolio and personal-finance vocabulary.
- `core_10` cards lead with question ownership and decision relevance before advanced math context.
- Every promoted KPI and promoted widget must keep one explicit comparison frame (`benchmark`, `prior period`, `target band`, or `concentration baseline`).
- Advanced metrics remain available but must not displace first-viewport interpretation copy.
- Every promoted entry must keep one plain-language interpretation sentence.
