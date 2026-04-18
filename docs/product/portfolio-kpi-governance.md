# Portfolio KPI And Widget Governance Catalog

## Purpose
Define one deterministic governance contract for promoted KPI and widget surfaces so interpretation tiering, route ownership, question-to-decision mapping, and comparison framing remain stable.

## Route Labels
| Route key | User-facing label | Lens | Interpretation job | Shell density | Executive first viewport template |
| --- | --- | --- | --- | --- | --- |
| `dashboard` | Executive morning briefing | `Overview` | Portfolio operating posture and highlights-first interpretation. | `expanded` | Dominant job: `home-primary-job`; Hero insight: `home-trend-preview`; Supporting: `home-kpi-strip`, `home-health-synthesis`, `home-hierarchy` |
| `holdings` | Holdings ledger workspace | `Holdings` | Position, lot, and concentration interpretation by instrument. | `standard` | Dominant job: `holdings-ledger-snapshot`; Hero insight: `holdings-ledger-pulse`; Supporting: holdings ledger table |
| `performance` | Benchmark-relative performance narrative | `Performance` | Attribution concentration and period-impact interpretation. | `standard` | Dominant job: `analytics-primary-job`; Hero insight: `analytics-trend`; Supporting: `analytics-contribution-leaders` |
| `risk` | Bounded estimator workspace | `Risk` | Downside and estimator posture interpretation with unit guardrails. | `compact` | Dominant job: `risk-primary-job`; Hero insight: estimator/risk context bridge; Supporting: drawdown + distribution before advanced diagnostics |
| `rebalancing` | Rebalancing and quant diagnostics | `Rebalancing` | Scenario comparison, optimization context, and forecast interpretation. | `compact` | Dominant job: `reports-primary-job`; Hero insight: quant scorecards; Supporting: lifecycle + Monte Carlo + contribution |
| `copilot` | Portfolio copilot | `Copilot` | Grounded narrative explanation with evidence-linked follow-ups. | `compact` | Chat-first workflow (outside executive operator first-viewport contract). |
| `transactions` | Cash operating console | `Cash/Transactions` | Deterministic cash-event and ledger-flow interpretation. | `standard` | Dominant job: `transactions-operating-job`; Hero insight: `transactions-ledger-pulse`; Supporting: `transactions-ledger-table` |

Legacy compatibility aliases remain supported for route migration:
`home -> dashboard`, `analytics -> performance`, `reports -> rebalancing`.

## Promoted Insight Governance Fields

All promoted (`primary`) widgets must include:

- Decision intent: one sentence describing what decision the module enables.
- Benchmark/target frame: explicit comparison context required to interpret value.
- Evidence depth: one of `first_surface_only`, `secondary_chart`, `companion_table`, `advanced_disclosure`.
- Chart relationship: one of `trend`, `ranking`, `distribution`, `contribution`, `performance_vs_target`, `state_summary`, `ledger`.
- Chart-fit rationale: why the chart form matches the data relationship.
- Prohibited alternatives: misleading chart forms that are not allowed without governance update.
- Accessible fallback: direct labels, summary text, and/or companion table requirements so first-surface interpretation is never hover-only.

## Chart-Fit Rules For Promoted Visuals

| Relationship | Approved form | Why it fits | Prohibited alternatives | Accessible fallback |
| --- | --- | --- | --- | --- |
| `trend` | line/timeline chart | Preserves sequence and slope interpretation for time-ordered movement. | pie/radar | latest + baseline labels, benchmark delta summary |
| `ranking` | ranked bars + table | Preserves ordering and cross-category magnitude comparison. | stacked-area, decorative donut | ranked companion table, top/bottom summary |
| `distribution` | histogram + tail summary | Preserves spread/skew/tail interpretation. | pie, stacked-line | bucket table and tail-mass text |
| `contribution` | diverging bars + ledger | Preserves signed magnitude and concentration interpretation. | single-value gauge | signed contribution ledger and leader/drag summary |
| `performance_vs_target` | benchmark/target referenced chart or card cluster | Keeps relative frame explicit in title/subtitle/legend. | isolated value without comparison | target and benchmark labels plus gap summary |
| `state_summary` | state cards / synthesis table | Supports decision framing and route orientation before drill-down. | dense mixed-axis composites | deterministic state sentence + status table |
| `ledger` | sortable table | Preserves deterministic event/row evidence path. | abstract heatmap without rows | row labels + filter state summary |

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
