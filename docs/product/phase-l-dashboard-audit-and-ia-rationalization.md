# Phase L Dashboard Audit And IA Rationalization

Date: 2026-04-05
Change: `phase-l-dashboard-audit-and-information-architecture-rationalization`

## 1. Widget Inventory Baseline

| Route | Widget ID | Visualization Type | Question Answered | Decision Enabled | Source Contract |
| --- | --- | --- | --- | --- | --- |
| Home | `home-primary-job` | Primary job panel | How is the portfolio operating overall right now? | Allocation review, income monitoring | `/api/portfolio/summary`, `/api/portfolio/time-series` |
| Home | `home-kpi-strip` | KPI cards | What are the core value/gain/income indicators? | Goal progress, allocation review | `/api/portfolio/summary`, `/api/portfolio/time-series` |
| Home | `home-health-synthesis` | Scorecards + semantic table | Which health pillars explain current posture? | Risk posture adjustment | `/api/portfolio/health-synthesis` |
| Home | `home-trend-preview` | Line chart | Is performance trend aligned with benchmark context? | Escalate to Risk vs Reports | `/api/portfolio/time-series` |
| Home | `home-hierarchy` | Hierarchy table | Where is allocation concentrated? | Diversification rebalance review | `/api/portfolio/hierarchy` |
| Home | `home-period-waterfall` | Waterfall | What bridge explains period movement? | Reconciliation check | `/api/portfolio/time-series`, `/api/portfolio/summary` |
| Home | `home-drilldown-routes` | Decision cards | Which route answers the next question fastest? | Route selection | Workspace route map |
| Analytics | `analytics-primary-job` | Primary job panel | Which attribution question should be interpreted first? | Concentration triage | `/api/portfolio/contribution` |
| Analytics | `analytics-trend` | Line chart | How has portfolio trend evolved versus benchmark? | Performance context before attribution | `/api/portfolio/time-series` |
| Analytics | `analytics-contribution-leaders` | Bar chart + table | Which symbols are top positive and negative contributors? | Concentration response | `/api/portfolio/contribution` |
| Analytics | `analytics-contribution-waterfall` | Waterfall | How do contribution steps bridge to total period impact? | Attribution decomposition detail | `/api/portfolio/contribution` |
| Risk | `risk-primary-job` | Primary job panel | What is current risk posture for selected scope? | Risk posture decision | `/api/portfolio/risk-estimators` |
| Risk | `risk-estimator-ledger` | Chart + method table | What do estimators and methods report now? | Validate risk tolerance fit | `/api/portfolio/risk-estimators` |
| Risk | `risk-health-bridge` | Context cards | How does risk posture affect health score? | Risk-to-goal adjustment | `/api/portfolio/health-synthesis` |
| Risk | `risk-drawdown` | Drawdown timeline | How deep and persistent is drawdown? | Downside tolerance check | `/api/portfolio/risk-evolution` |
| Risk | `risk-return-distribution` | Histogram | What is the shape of returns distribution? | Tail-risk awareness | `/api/portfolio/return-distribution` |
| Risk | `risk-rolling-estimator` | Rolling timeline | Are volatility/beta regimes shifting? | Regime-change monitoring | `/api/portfolio/risk-evolution` |
| Risk | `risk-correlation-network` | Correlation matrix + links | Where is hidden co-movement concentration? | Correlation-aware concentration action | `/api/portfolio/summary`, `/api/portfolio/time-series` |
| Risk | `risk-tail-diagnostics` | Tail cards + ledger | How severe are left-tail scenarios? | Stress-loss guardrail decision | `/api/portfolio/risk-estimators`, `/api/portfolio/return-distribution` |
| Reports | `reports-primary-job` | Primary job panel | Are confidence and goal signals strong enough for reporting? | Report readiness | `/api/portfolio/quant-metrics`, `/api/portfolio/monte-carlo` |
| Reports | `reports-quant-scorecards` | Metric cards + table | What core quant diagnostics say for this period? | Performance quality interpretation | `/api/portfolio/quant-metrics` |
| Reports | `reports-lifecycle` | Lifecycle panel | Is report artifact lifecycle ready? | Generate/export decision | `/api/portfolio/quant-reports`, `/api/portfolio/quant-reports/{report_id}` |
| Reports | `reports-monte-carlo` | Scenario diagnostics | What are bounded bust/goal probabilities? | Threshold policy adjustment | `/api/portfolio/monte-carlo` |
| Reports | `reports-monthly-heatmap` | Heatmap | What monthly return rhythm appears? | Regime context | `/api/portfolio/time-series` |
| Reports | `reports-symbol-focus` | Contribution focus table | Which symbols need deeper report scope? | Scope narrowing to instrument | `/api/portfolio/contribution` |
| Reports | `reports-advanced-risk-lab` | Frontier + budget tables | How frontier allocations compare with contribution concentration? | Frontier-aware allocation review | `/api/portfolio/efficient-frontier`, `/api/portfolio/contribution` |
| Reports | `reports-ml-insights` | Signal/forecast/registry tower | Are ML diagnostics and governance states ready? | ML readiness gating | `/api/portfolio/ml/signals`, `/api/portfolio/ml/forecasts`, `/api/portfolio/ml/registry` |
| Reports | `reports-health-bridge` | Scenario bridge cards | Does health posture align with scenario outputs? | Health posture calibration | `/api/portfolio/health-synthesis`, `/api/portfolio/monte-carlo` |
| Transactions | `transactions-ledger-table` | Filterable table | What deterministic cash and quantity events occurred? | Cash-flow and ledger validation | `/api/portfolio/transactions` |

## 2. Heuristic + Visualization Findings

| Finding | Severity | Impact | Notes |
| --- | --- | --- | --- |
| Too many equal-priority modules in Risk and Reports first surface | High | Slower 5-second scan, harder triage | Addressed via progressive disclosure toggles |
| Duplicate attribution framing in Analytics (`leaders` + `waterfall`) at equal priority | Medium | Repeated cognitive load | Waterfall moved to advanced disclosure |
| Shell chrome competed with dense analytical routes | High | Primary analysis starts below utility surfaces | Route-aware shell density modes added (`expanded/balanced/compact`) |
| Route labels lacked explicit lens context | Medium | Harder mental model transfer between routes | Lens chips and lens copy added to workspace nav |
| Advanced modules lacked deterministic gating contract | High | Regressions likely as modules are added | Governance + fail-first IA tests added |

## 3. Disposition Decisions (`KEEP` / `MERGE` / `MOVE` / `REMOVE`)

| Widget | Decision | Severity | Rationale | Destination / Replacement Behavior |
| --- | --- | --- | --- | --- |
| `analytics-contribution-leaders` | KEEP | Medium | Canonical attribution view with ranked concentration + table semantics | Remains primary in Analytics |
| `analytics-contribution-waterfall` | MOVE | Medium | Useful decomposition but duplicates primary question in first surface | Moved behind explicit advanced disclosure in Analytics |
| `risk-rolling-estimator` | MOVE | High | Valuable but not required for first scan | Moved to advanced disclosure in Risk |
| `risk-correlation-network` | MOVE | High | Heavy interpretation cost; secondary for most sessions | Moved to advanced disclosure in Risk |
| `risk-tail-diagnostics` | MOVE | High | Secondary interpretation after baseline risk checks | Moved to advanced disclosure in Risk |
| `reports-advanced-risk-lab` | MOVE | High | Advanced optimization context, not first-surface requirement | Moved behind advanced disclosure in Reports |
| `reports-ml-insights` | MOVE | High | Governance-heavy diagnostics for secondary analysis | Moved behind advanced disclosure in Reports |
| `reports-health-bridge` | MOVE | Medium | Useful cross-check, but post-primary interpretation | Moved behind advanced disclosure in Reports |
| Route-jump labels without lens framing | MERGE | Medium | Route name + lens meaning were disconnected | Merged via nav lens chip + monitoring-lens copy |
| Any duplicated primary question keys per route | REMOVE (contract) | High | Equal-priority duplication violates IA budget and scanability | Prevented by fail-first governance tests |

## 4. Route-To-Lens Mapping

| Lens | Primary Routes | Secondary / Drill-down |
| --- | --- | --- |
| Overview | `/portfolio/home` | `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/reports`, `/portfolio/transactions` |
| Holdings | `/portfolio` grouped summary, `/portfolio/:symbol` lot detail | `/portfolio/home` hierarchy snapshot |
| Performance | `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/reports` | Home trend preview + drill-down links |
| Cash/Transactions | `/portfolio/transactions` | Home drill-down cards |

## 5. Textual Wireframes

### 5.1 Overview (`/portfolio/home`)
- First surface:
  - Primary job panel
  - KPI strip
  - Trend preview
  - Hierarchy snapshot
- Secondary surface:
  - Health synthesis table
  - Period bridge waterfall
  - Drill-down route cards

### 5.2 Performance Attribution (`/portfolio/analytics`)
- First surface:
  - Primary job panel
  - Trend chart
  - Contribution leaders chart + table
- Progressive disclosure:
  - Attribution waterfall bridge

### 5.3 Performance Risk (`/portfolio/risk`)
- First surface:
  - Primary job panel
  - Estimator ledger
  - Health context bridge
  - Drawdown timeline
  - Return distribution
- Progressive disclosure:
  - Rolling estimators timeline
  - Correlation network
  - Tail risk diagnostics

### 5.4 Performance Quant (`/portfolio/reports`)
- First surface:
  - Primary job panel
  - Quant scorecards
  - Report lifecycle
  - Monte Carlo diagnostics
  - Monthly heatmap
  - Symbol contribution focus
- Progressive disclosure:
  - Advanced risk lab
  - ML insights control tower
  - Health scenario bridge

### 5.5 Cash/Transactions (`/portfolio/transactions`)
- First surface:
  - State banner
  - Filter controls
  - Deterministic ledger event table
- Deferred:
  - No market-refresh diagnostics in v1 route
