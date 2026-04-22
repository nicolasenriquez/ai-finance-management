# Two-Tab Dashboard Wireframe v1

## Superseded By Third-Pass Refinement

This wireframe reflects the earlier compact-dashboard iteration.
For implementation-facing refinement, use:

- [portfolio-dashboard-third-pass-refinement.md](./portfolio-dashboard-third-pass-refinement.md)

The third-pass memo supersedes the route/chart distribution guidance in this file.

## Scope

This document defines the implementation wireframe for the new personal investing cockpit with two tabs maximum:

- `Opportunities` (default)
- `My Portfolio`

The goal is execution clarity for a long-term investor. This is a build blueprint, not a moodboard.

## Hard Constraints

- Two first-level tabs maximum.
- First viewport must answer the main decision without long scroll.
- No hidden critical state in hover-only UI.
- Modules without real data contracts must render explicit `unavailable`.
- Didactic copy is required on all primary modules.
- `pandas` is computation-only; displayed metrics need explicit data provenance.
- `buy/add` states require fresh-enough evidence; otherwise degrade to `wait` or `unavailable`.
- Primary modules must follow `what -> why -> action -> evidence` storytelling sequence.
- Layout rhythm uses phi-derived ratio (`1.613`) for spacing and module cadence.
- Large rounded emphasis controls (`100` / `135` pill style) are allowed only for high-emphasis chips and actions.
- Loading skeletons must preserve stable geometry (no abrupt layout jump when data resolves).

## Layout System

- Desktop grid: 12 columns.
- Max content width: 1360px.
- First viewport budget (desktop): <= 900px total height.
- Section spacing scale: 8px base.
- Motion: 150-220ms, `ease-out`, reduced-motion respected.

Phi-derived rhythm tokens (rounded approximations):

- spacing: `8, 13, 21, 34, 55`
- vertical module cadence targets: `233, 377, 610`
- enforce usability override: if phi-token use harms readability/tap targets, use accessible fallback

## Tab 1: Opportunities (Default)

### Desktop Wireframe

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Global Header: product + period + symbol search + refresh + profile        │
├─────────────────────────────────────────────────────────────────────────────┤
│ Tabs: [Opportunities] [My Portfolio]                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ OP-01 Market Strip (12 cols)                                               │
│ Compact watchlist/index row: symbol, last, %change, state, sharpe/risk    │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ OP-02 Opportunity Table       │ OP-03 Selected Opportunity Hero            │
│ (5 cols, h~360)               │ (7 cols, h~360)                            │
│ Ranked list + quick chips     │ Main decision card + didactic explanation  │
├───────────────────────────────┴─────────────────────────────────────────────┤
│ OP-04 Risk Management Bar (12 cols, h~180)                                 │
│ Inputs + computed size/stop/target/r:r + recommendation state              │
├─────────────────────────────────────────────────────────────────────────────┤
│ OP-05 Evidence Drawer (collapsed by default)                               │
│ Fundamentals / Technical / Thesis / Contract status                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
Header
Tabs
OP-03 Selected Opportunity Hero
OP-04 Risk Management Bar
OP-02 Opportunity Table (virtualized list)
OP-01 Market Strip (horizontal chips)
OP-05 Evidence Drawer
```

Mobile rule: Hero and Risk Bar stay above list for decision-first behavior.

## Tab 2: My Portfolio

### Desktop Wireframe

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Global Header + Tabs                                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│ PF-01 KPI Strip (12 cols)                                                  │
│ Market value | Unrealized | Realized | Dividend | Concentration            │
├───────────────────────────────────────────┬─────────────────────────────────┤
│ PF-02 Performance Time Series (8 cols)    │ PF-03 Strengths/Weaknesses      │
│ Portfolio vs benchmark + period selector  │ (4 cols) top winners/laggards   │
├───────────────────────────────┬─────────────────────────────────────────────┤
│ PF-04 Exposure/Contribution   │ PF-05 Hierarchy Pivot Table                │
│ (4 cols, bars)                │ (8 cols) preserve expand/collapse/sort     │
├─────────────────────────────────────────────────────────────────────────────┤
│ PF-06 Report Lifecycle Panel (collapsed by default on desktop)             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Mobile Wireframe

```text
Header
Tabs
PF-01 KPI Strip (2x3 cards)
PF-02 Performance Time Series
PF-03 Strengths/Weaknesses
PF-04 Exposure/Contribution
PF-05 Hierarchy Pivot
PF-06 Report Lifecycle
```

## Component Inventory (Primary)

### Opportunities

- `OP-01` Market Strip
- `OP-02` Opportunity Table
- `OP-03` Selected Opportunity Hero
- `OP-04` Risk Management Bar
- `OP-05` Evidence Drawer

### My Portfolio

- `PF-01` KPI Strip
- `PF-02` Performance Time Series
- `PF-03` Strengths/Weaknesses
- `PF-04` Exposure/Contribution
- `PF-05` Hierarchy Pivot Table
- `PF-06` Report Lifecycle Panel

## Data Mapping to Existing API Contracts

| Component | Endpoint(s) | Core Fields | Unsupported/Fallback |
| --- | --- | --- | --- |
| `OP-01` | `GET /api/portfolio/summary` | `rows[].instrument_symbol`, `market_value_usd`, `unrealized_gain_pct` | If trend/signal fields unavailable, show `state: unknown` |
| `OP-02` | `POST /api/portfolio/copilot/chat` (`operation: opportunity_scan`) | `opportunity_candidates[]`, `action_state`, `opportunity_score`, `drawdown_from_52w_high_pct`, `return_30d`, `return_90d`, `volatility_30d` | If scan unavailable, show `scanner unavailable` |
| `OP-03` | same as `OP-02` + `GET /api/portfolio/time-series` | selected symbol metrics + trend context | Fundamental proprietary signals remain `unavailable` |
| `OP-04` | local calculation + selected symbol context | account size, risk%, stop%, entry, target | If entry/volatility unavailable, disable CTA and explain |
| `PF-01` | `GET /api/portfolio/summary` | aggregated totals | none |
| `PF-02` | `GET /api/portfolio/time-series` | `points[]`, benchmark fields | if benchmark omitted, show explicit omission copy |
| `PF-03` | `GET /api/portfolio/contribution` | top/bottom `contribution_pnl_usd` | none |
| `PF-04` | `GET /api/portfolio/exposure` (if available), else summary-derived buckets | exposure weights | if endpoint unavailable, fallback to summary-derived exposure |
| `PF-05` | existing hierarchy query path | grouped rows, sorting, expand/collapse | none |
| `PF-06` | quant report endpoints | lifecycle states and report links | none |

`PF-06` compact gadget contract:

- keep `Generate HTML report`
- keep `Export analyst pack (.md)`
- include scope selector (`portfolio`, symbol-level)
- include date range controls (preset + calendar range)
- lifecycle chips remain explicit and keyboard reachable

## YFinance Extraction Map (v1 Baseline)

| Metric/Module intent | yfinance path now | Availability in v1 |
| --- | --- | --- |
| OHLCV and trend inputs | `download` / `Ticker.history` | `direct` |
| Corporate actions context | `actions` / `dividends` / `splits` | `direct` |
| Valuation and quality base | `Ticker.info` + financial tables | `direct` (coverage varies by ticker) |
| Additional ratio universe | `EquityQuery`/`screen` fields (valuation, profitability, leverage, liquidity) | `direct` for supported fields |
| Options IV context | `option_chain(...).calls/puts` `impliedVolatility` column | `direct` (contract-level) |
| ATR / MA regime / support-resistance | pandas-derived from OHLCV | `derived` |
| Risk bar position sizing | local formula + price inputs | `derived` |
| J5 / JR4 / proprietary labels | not native in yfinance | `unavailable` unless custom rule engine implemented |
| Historical IV percentile series | not first-class in yfinance docs/API | `unavailable` by default |

Rule:

- before rendering `unavailable`, the implementation must verify `direct` and `derived` paths above.

## Data Provenance Contract

Every decision-critical card must show compact provenance metadata:

- source badge: `direct`, `derived`, or `proxy`
- freshness badge: `fresh`, `delayed`, `stale`, or `unavailable`
- `as_of` timestamp

Rule:

- if freshness is `stale` or confidence is `proxy` for required factors, CTA state cannot be `buy` or `add`.

## Signal State Machine (Decision Engine v1)

Inputs:

- trend regime (`bull`, `neutral`, `bear`)
- confirmation set (`green_on_green`, `red_on_red`, `j5`, `jr4`)
- overextension flags (cyan-run count, distance-from-mean)
- risk-fit (`risk_reward_ratio`, stop validity)
- contract confidence and freshness

Output states:

- `buy`: confirmation + risk-fit + freshness all pass
- `add`: existing position + confirmation + risk-fit pass
- `wait`: setup incomplete, overextended, or confidence below threshold
- `avoid`: bearish or risk-invalid structure
- `unavailable`: missing or stale critical contracts

## Blast Radius Guardrails

- Provider or contract failure in `OP-*` modules cannot block `PF-*` modules.
- Each module has its own error boundary and unavailable-state copy.
- Fallback order is strict: `direct -> derived -> unavailable`.
- No cross-module silent fallback to guessed values.

## Opportunity Score v1 (Didactic, Deterministic)

Use weighted scoring with visible factors:

- `valuation_score` (0-100)
- `quality_score` (0-100)
- `timing_score` (0-100)
- `risk_fit_score` (0-100)

`opportunity_score = 0.35*valuation + 0.25*quality + 0.20*timing + 0.20*risk_fit`

If a factor lacks contract data, mark factor `unavailable` and rescale remaining weights visibly.

## Risk Management Bar Formula

Inputs:

- `account_size`
- `risk_pct`
- `entry_price`
- `stop_pct`
- `target_price`

Derived:

- `max_risk_dollars = account_size * risk_pct`
- `stop_price = entry_price * (1 - stop_pct)`
- `risk_per_share = entry_price - stop_price`
- `position_size = floor(max_risk_dollars / risk_per_share)` if `risk_per_share > 0`
- `expected_reward_per_share = target_price - entry_price`
- `risk_reward_ratio = expected_reward_per_share / risk_per_share`

Display state:

- `buy/add candidate` if ratio and signal constraints pass
- `wait` when setup quality is weak
- `avoid` when risk structure is invalid
- `unavailable` when critical inputs are stale, missing, or contractless

## Didactic Copy Contract

Each primary card must render:

- `What`: short label and current value/state
- `Why`: one sentence interpretation
- `Action`: one sentence recommendation (`buy`, `add`, `wait`, `avoid`)

Example:

- `What`: "Valuation context: 14% discount to fair value proxy"
- `Why`: "Price is below baseline valuation range while quality remains stable."
- `Action`: "Wait for technical confirmation before adding size."

## Storytelling Contract (Primary Modules)

Each primary module must render in this order:

1. `What`: current state or metric
2. `Why`: interpretation
3. `Action`: buy/add/wait/avoid guidance or portfolio action
4. `Evidence`: source + freshness + confidence metadata

## Interaction Flows

### Flow A: Opportunity Scan

1. User lands on `Opportunities`.
2. System loads `OP-02` ranked list.
3. First row auto-selects into `OP-03`.
4. User tweaks risk inputs in `OP-04`.
5. Recommendation state updates in real time.
6. User opens `OP-05` for evidence.

### Flow B: Portfolio Review

1. User switches to `My Portfolio`.
2. `PF-01` and `PF-02` load first.
3. User inspects `PF-03` leaders/laggards.
4. User drills into `PF-05` hierarchy and lots.
5. User opens `PF-06` only if report action is needed.

## Empty / Error / Unavailable States

- Empty watchlist: "No opportunities yet. Run scan to generate candidates."
- Scanner error: "Opportunity scan unavailable. Retry or continue with portfolio review."
- Missing contract metric: "Research metric not connected yet. Showing available factors only."
- Loading: preserve panel skeleton with stable heights.

## Anti-Bloat Guardrails

- Max 5 primary blocks in `Opportunities`.
- Max 6 primary blocks in `My Portfolio`.
- No third top-level tab without explicit OpenSpec change.
- No full-page new route for analytics unless a current tab cannot contain it with bounded disclosure.

## Implementation Sequence

1. Build shell + tabs + responsive layout.
2. Implement provenance/freshness metadata plumbing and module-level error boundaries.
3. Implement `Opportunities` first viewport (`OP-01..OP-04`).
4. Implement `My Portfolio` first viewport (`PF-01..PF-04`).
5. Reuse and adapt hierarchy table (`PF-05`).
6. Integrate report lifecycle panel (`PF-06`).
7. Add evidence drawers and didactic copy.
8. Add unavailable-contract states, feature flags, and final polish.

## Acceptance Criteria (Wireframe Level)

- Two tabs only.
- `Opportunities` default.
- First viewport answers decision in <10 seconds.
- No critical decision requires scroll to be understood.
- Unsupported metrics never appear as fake values.
- Desktop and mobile both preserve dominant-action clarity.
