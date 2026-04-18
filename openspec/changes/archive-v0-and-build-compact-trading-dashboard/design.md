## Context

`phase-n-dashboard-professionalization-and-executive-workspace-system` improved the current workspace, but it still assumes a route-heavy analytical product. That is no longer the right target.

The user now wants:

- a dashboard that starts from zero
- a much smaller surface
- a didactic experience
- a first major view centered on portfolio state
- subsequent views for explainability, downside risk, tactical review, and asset-level detail
- a five-route architecture rather than a tabbed workspace
- little dependence on vertical scrolling

The user explicitly does **not** want a redesign that mainly recycles the existing AI Finance Management frontend shell.

Repository reality:

- the current frontend and some docs are already dirty in the worktree
- the repo already exposes useful typed portfolio/risk/quant/report APIs
- the repo does not yet expose a full first-class contract for many of the fundamental and proprietary technical metrics the user wants to see

Therefore the redesign must separate:

- metrics we can power now
- metrics we can design for but must render as unavailable until a data contract exists

## Goals / Non-Goals

**Goals**

- Archive the current frontend into `/v0` before replacement work.
- Rebuild the active frontend as a compact five-route personal investing cockpit.
- Make `/portfolio/home` the dominant landing route.
- Keep `analytics`, `risk`, `signals`, and `asset-detail` as purposeful follow-on routes.
- Keep first-viewport clarity as a hard requirement.
- Keep unsupported research metrics explicit and fail-fast.
- Preserve only the existing behaviors that still materially improve the new design.

**Non-Goals**

- Reworking backend analytics formulas in this planning step.
- Preserving current route topology, shell behavior, or page structure by default.
- Pretending the repo already has true `P/E`, `P/S`, `Rule of 40`, `J5`, `JR4`, volume profile, or green-on-green APIs.
- Shipping production code in this proposal step.

## Decisions

### Decision: Archive current frontend into `/v0` before replacement

The current frontend should be preserved as a recoverable artifact, not partially refactored in place.

Recommended shape:

- `v0/frontend-legacy/`
- archive README summarizing what was preserved
- active `frontend/` rebuilt after archive step

Rationale:

- the user wants the previous UI saved
- this lowers replacement risk
- it prevents accidental complexity from carrying forward

### Decision: Replace the multi-route workspace with a five-route executive shell

The live product should revolve around one compact route family:

- `/portfolio/home`
- `/portfolio/analytics`
- `/portfolio/risk`
- `/portfolio/signals`
- `/portfolio/asset-detail/:ticker`

Rationale:

- the user’s third-pass refinement explicitly calls for route separation by business question
- `building-dashboards` favors one dominant question per surface and bounded module counts
- a route family better matches the real jobs:
  - executive state
  - explainability
  - downside control
  - tactical review
  - instrument detail

Alternatives considered:

- keep the two-tab shell and compress everything into tabs: rejected because it keeps too much category mixing and makes route differentiation weaker

### Decision: Make `/portfolio/home` the default and dominant route

This route should answer:

- how is my portfolio doing right now?
- how am I doing vs benchmark?
- what needs attention immediately?

Recommended first viewport:

- KPI strip
- equity curve vs benchmark
- attention panel
- top movers

Recommended deeper surfaces:

- allocation snapshot
- holdings summary table
- compact report utility

Rationale:

- the user wants the executive answer in 5–8 seconds
- the portfolio story should start with state, not with tactical signals

### Decision: Make `analytics`, `risk`, `signals`, and `asset-detail` explicit follow-on routes

These routes should answer:

- `analytics`: why did the portfolio move?
- `risk`: how fragile is the portfolio?
- `signals`: which assets deserve tactical review? The user-facing page label may render as `Opportunities`.
- `asset-detail`: what is happening with this asset?

Rationale:

- route differentiation reduces clutter and repeated visuals
- it keeps the main overview clean while preserving analytical depth
- it provides a clearer executive -> interpretive -> tactical -> instrument drill-down sequence

### Decision: Prioritize research-backed metric groups

The dashboard should emphasize four metric groups.

#### 1. Opportunity valuation metrics

- fair value discount/premium
- `P/E`
- `P/S`
- `P/B`
- `P/CF`
- `PEG`

Why:

- Fidelity's valuation-ratio guide highlights `P/E`, `P/S`, `P/B`, `P/CF`, and `PEG`
- Morningstar centers fair value, rating, and uncertainty in stock research

#### 2. Business quality metrics

- operating margin
- free cash flow
- `ROE`
- `ROIC`
- debt-to-equity
- current ratio

Why:

- Fidelity management-ratio guidance highlights operating margin, free cash flow, `ROE`, `ROIC`, and current ratio
- Schwab highlights `ROE` and debt-to-equity as core stock-analysis ratios

#### 3. Timing and execution metrics

- 50D / 200D regime
- support and resistance
- ATR
- trail stop
- risk/reward
- action state: buy / add / wait / avoid

Why:

- Schwab technical guidance emphasizes moving averages, support/resistance, and ATR
- the provided transcript emphasizes confirmation, risk sizing, and avoiding emotional chasing

#### 4. Portfolio-control metrics

- market value
- unrealized gain/loss
- realized gain/loss
- dividend income
- concentration
- sector exposure
- winners/laggards
- performance over time

Why:

- Koyfin portfolio tools emphasize portfolio-level return summaries
- Fidelity diversification guidance emphasizes exposure control

### Decision: Keep unsupported research modules explicit

Bucket A, supported now by current repo APIs:

- summary
- hierarchy and lots
- time series
- contribution
- risk estimators
- risk evolution
- quant metrics
- report lifecycle
- opportunity proxy signals

Bucket B, future enrichment contract required:

- true `P/E`, `P/S`, `P/B`, `P/CF`, `PEG` if not already available from a source boundary
- operating margin
- free cash flow margin
- debt-to-equity
- current ratio
- Rule of 40
- FNR
- 5R family
- `J5`
- `JR4`
- blue-arrow confirmation
- green-on-green / red-on-red
- volume profile
- IV percentile
- cyan-bar exhaustion count

Bucket C, UI state until contracts exist:

- `unavailable`
- `research data pending`
- `signal contract not connected`

Rationale:

- the repo already treats fundamentals enrichment as a separate boundary
- fail-fast behavior is a repo rule
- the new UI must be trusted, not theatrical

### Decision: Formalize source contracts before exposing advanced signals

The redesign must separate computation tooling from data origin and lock provenance by metric family.

Source model:

- `pandas`: transformation and indicator-calculation layer only
- source contracts:
  - `prices`: OHLCV and returns inputs
  - `fundamentals`: statements, ratios, quality metrics
  - `reference`: symbol metadata, sector mapping, benchmark mapping
  - `signals`: deterministic outputs derived from `prices` and rules
- each rendered metric includes:
  - `source_id`
  - `as_of`
  - `freshness_state` (`fresh`, `stale`, `delayed`, `unavailable`)
  - `confidence_state` (`direct`, `derived`, `proxy`)

Bootstrap source policy:

- `yfinance` is the primary data source for this redesign phase
- `pandas` computes derived indicators from `yfinance` time series and financial tables
- provider migration is not a blocker for this phase; what matters now is maximizing reliable extraction from the current source
- still apply provenance/freshness gating so stale or missing evidence never upgrades state to `buy` or `add`

Rationale:

- user asked for senior-level blind-spot control, not just UI polish
- repository fail-fast rules require explicitness when contracts are weak
- this avoids fake certainty in buy/add/wait decisions

### Decision: Prioritize metrics already available in yfinance

Before marking research modules as unavailable, the implementation must first exhaust what yfinance already exposes directly or via deterministic derivation.

Coverage categories:

- `Direct`:
  - `Ticker.history` and `download` for OHLCV
  - `actions`, `dividends`, `splits`
  - financial statements: income, balance, cashflow (yearly, quarterly, trailing)
  - analysis/estimates/holders/news modules
  - options chain with `impliedVolatility` at contract level
- `Direct via screener fields` (`EquityQuery`/`screen`):
  - valuation/profitability/leverage/liquidity fields including `peratio.lasttwelvemonths`, `pegratio_5y`, `pricebookratio.quarterly`, `returnonassets.lasttwelvemonths`, `returnonequity.lasttwelvemonths`, `totaldebtequity.lasttwelvemonths`, `currentratio.lasttwelvemonths`, and more
- `Derived with pandas`:
  - ATR, moving-average regime, support/resistance heuristics, risk/reward, Sharpe, overextension counters
- `Not native in yfinance`:
  - proprietary labels/signals (`J5`, `JR4`, green-on-green, red-on-red) unless implemented as custom deterministic overlays
  - historical IV percentile as a first-class built-in series

Rationale:

- user requested focus on currently available data, not provider upgrades
- yfinance documentation and API surface are broad enough to unlock more value immediately
- this keeps scope pragmatic while preserving trust through explicit confidence states

### Decision: Add a blind-spot register and blast-radius controls

Known blind spots:

- delayed/stale market prints
- split/dividend adjustment mismatches
- timezone/session boundary drift
- missing fundamentals/ratios for certain symbols, markets, ADRs, or listing ages
- lookahead bias in technical calculations
- yfinance/Yahoo response anomalies, throttling, or transient failures

Required controls:

- freshness SLA per metric group with visible expiry in UI
- deterministic fallback order (`direct -> derived -> unavailable`, never silent substitute)
- server-side caching and request budgets for yfinance extraction paths
- feature flags for high-risk modules (`advanced_signals_enabled`, `fundamentals_contract_v1`)
- provenance logging for decision cards (inputs, timestamp, contract version)
- kill-switch to hide compromised modules without breaking the whole dashboard

Rationale:

- protects user trust during data incidents
- limits blast radius to a module instead of the full dashboard
- enables controlled rollout from bootstrap feeds to stricter contracts

### Decision: Use a didactic UX, not a pure terminal clone

Every key module should explain:

- what it is
- why it matters
- what the investor should consider doing

Recommended micro-pattern:

- metric or chart
- one-sentence interpretation
- one-sentence action framing

Rationale:

- the user explicitly wants the dashboard to be very didactic
- raw density without explanation would recreate the current problem in another style

### Decision: Use institutional premium styling, not generic AI SaaS styling

Recommended visual direction:

- deep ink and petroleum surfaces
- strong but restrained blue/teal/amber/rose semantics
- modern sans for narrative and UI
- tabular numeric type for metrics
- motion used sparingly
- no purple bias

Rationale:

- aligns with the user's references
- aligns with `ui-ux-pro-max` accessibility and hierarchy guidance
- ages better than novelty styling

### Decision: Encode storytelling as a first-class UI contract

Each primary module in both tabs should follow one compact narrative sequence:

- Context (`what`)
- Interpretation (`why`)
- Action (`now what`)
- Evidence (`show source and confidence`)

Per-tab storyline:

- `Opportunities` / `signals`: market context -> candidate ranking -> selected setup -> risk sizing -> evidence drawer
- `My Portfolio`: current snapshot -> trend -> attribution/exposure -> preserve/report actions

Rationale:

- user requested explicit storytelling and didactic behavior
- this prevents dense modules from feeling disconnected
- this gives deterministic reading order for both humans and LLM-generated UI updates

### Decision: Use colocated, compositional route-component architecture

Frontend implementation should default to component directories that colocate:

- component implementation
- tests
- route-local hooks when complexity justifies them
- route-local types when they are not broadly shared

Component rules:

- prefer composition over configuration-heavy wrappers
- keep presentation components focused on rendering
- keep data loading and remote-state orchestration in container components or hooks
- avoid prop drilling deeper than three levels by restructuring ownership or using narrowly scoped context
- split components that exceed practical reviewability instead of allowing route files to become dumping grounds

Rationale:

- aligns the redesign with production frontend engineering rather than mockup-style assembly
- reduces coupling between route shells, data access, and rendering primitives
- makes the five-route cockpit maintainable as more modules become real

### Decision: Make accessibility, responsiveness, and state feedback contractual

The rebuilt frontend should treat these as acceptance criteria, not polish:

- keyboard-accessible interactive controls
- semantic heading hierarchy and form/control labels
- visible focus states
- non-color-only state communication
- meaningful loading, empty, unavailable, and error states
- mobile-first behavior validated at `320`, `768`, `1024`, and `1440`
- no horizontal overflow on primary routes

Interaction and motion rules:

- use skeletons instead of spinner-only content loading for primary modules
- keep motion subtle, purposeful, and compatible with reduced-motion preferences
- preserve layout stability during async state changes

Rationale:

- the product is data-dense and must remain operable under keyboard, screen-reader, and narrow-screen conditions
- compact dashboards fail quickly when empty/error/loading states are treated as afterthoughts
- this closes the gap between design intent and production-grade frontend behavior

### Decision: Reject AI-default styling and enforce semantic UI tokens

The redesign should explicitly avoid generic generated-dashboard patterns:

- no purple/indigo-by-default palette
- no raw hex usage in route-level components when semantic tokens exist
- no arbitrary off-scale spacing values
- no maximum-radius-everywhere card language
- no filler hero sections or generic card grids that ignore information priority

Visual implementation should prefer:

- semantic color, spacing, typography, border, and radius tokens
- content-first layout with clear priority and density control
- restrained shadows and gradients
- tabular-number treatment where financial comparison depends on numeric alignment

Rationale:

- the user wants a serious portfolio intelligence product, not a generic AI SaaS skin
- semantic tokens keep the system coherent as the five routes expand
- information hierarchy matters more than decorative novelty in finance surfaces

### Decision: Use phi-derived spacing rhythm and explicit corner tokens

Adopt a phi-based sizing rhythm anchored on the requested ratio (`1.613`) for visual harmony:

- spacing rhythm (approx): `8, 13, 21, 34, 55`
- module height rhythm (approx): `233, 377, 610` where possible
- keep first viewport budget hard-limited to avoid tall stacks

Corner system:

- default data cards: moderate radius tokens
- emphasis chips and hero controls: large pill tokens mapped to requested `100` and `135` rounded styles
- avoid mixed/random corner styles within the same module family

Rationale:

- user explicitly requested harmonic spacing and rounded-style consistency
- predictable tokens improve visual quality and implementation consistency
- explicit tokens reduce UI drift during future iterations

### Decision: Preserve Quant report actions as a compact portfolio gadget

`My Portfolio` must retain a compact report gadget that keeps:

- `Generate HTML report`
- `Export analyst pack (.md)`
- scope selection (portfolio vs instrument)
- date-range selection (calendar input + presets)

Placement and behavior:

- secondary visual priority (lower in panel hierarchy, bounded height)
- persistent action surface (not hidden in hover or deep modal chains)
- full lifecycle states remain explicit (`requested`, `generated`, `preview_ready`, `error`, `unavailable`)

Rationale:

- user explicitly requested this functionality be preserved
- current workflow already provides deterministic lifecycle behavior worth keeping
- compact gadget placement keeps utility without bloating the main decision viewport

### Decision: Apply skeleton-loading strategy to preserve layout stability

Adopt `boneyard`-style skeletons as loading references for dashboard modules:

- stable dimensions per module state
- no CLS-like jump between loading and ready states
- skeleton hierarchy aligned to final information hierarchy

Rationale:

- improves perceived performance while data contracts resolve
- supports didactic, low-noise loading behavior
- aligns with compact dashboard constraints where layout jumping is expensive

## Risks / Trade-offs

- [The five-route shell regrows into a route maze] -> codify route ownership, default entry, and module budgets in contracts and tests.
- [The home route becomes too trader-like for a long-term investor] -> keep valuation and business quality ahead of tactical signals in the information hierarchy.
- [The UI implies unsupported precision] -> render missing research modules as unavailable and explain why.
- [Too much old UI leaks into the new product] -> preserve only approved behaviors, not page structures.
- [The didactic layer becomes verbose] -> keep explanations compact and expandable.
- [Bootstrap sources are treated as institutional truth] -> keep provenance/freshness badges and block hard action states when confidence is below threshold.
- [Data-provider failures cascade across routes] -> isolate contracts by module and enforce kill-switch plus graceful unavailable states.
- [Golden-ratio rules are over-applied and hurt usability] -> treat phi rhythm as guiding tokens, not a rigid constraint against readability or accessibility.
- [Large corner tokens reduce data density on smaller screens] -> limit `100/135` pill tokens to emphasis controls and preserve tighter card radii for tables/charts.

## Migration Plan

1. Freeze the five-route information architecture and preserve list.
2. Archive the current frontend into `/v0` with a manifest.
3. Scaffold a clean active `frontend/`.
4. Define source contracts, freshness rules, and provenance metadata per metric family.
5. Reuse only foundations that still fit:
   - API client
   - schemas
   - formatting
   - lifecycle states
6. Implement `/portfolio/home` first.
7. Implement `/portfolio/analytics` second.
8. Implement `/portfolio/risk` third.
9. Implement `/portfolio/signals` fourth.
10. Implement `/portfolio/asset-detail/:ticker` fifth.
11. Add explicit unavailable states for unsupported research modules.
12. Enable advanced modules behind feature flags and staged rollout.

Rollback:

- keep `v0/frontend-legacy/` recoverable
- keep backend contracts unchanged so UI rollback remains independent

## External Research Basis

- Fidelity valuation ratios: https://www.fidelity.com/learning-center/trading-investing/fundamental-analysis/company-valuation-ratios
- Fidelity management/growth ratios: https://www.fidelity.com/learning-center/trading-investing/fundamental-analysis/management-growth-ratios
- Fidelity position management: https://www.fidelity.com/learning-center/trading-investing/trading/managing-positions
- Fidelity diversification: https://www.fidelity.com/learning-center/trading-investing/diversification
- Schwab fundamentals vs technicals: https://www.schwab.com/learn/story/how-to-pick-stocks-using-fundamental-and-technical-analysis
- Schwab moving averages: https://www.schwab.com/learn/story/how-to-trade-simple-moving-averages
- Schwab ATR: https://www.schwab.com/learn/story/average-true-range-indicator-and-volatility
- Schwab key financial ratios: https://www.schwab.com/learn/story/five-key-financial-ratios-stock-analysis
- yfinance legal and API docs: https://ranaroussi.github.io/yfinance/index.html
- yfinance ticker API: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- yfinance download API: https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- yfinance financials reference: https://ranaroussi.github.io/yfinance/reference/yfinance.financials.html
- yfinance screener query fields: https://ranaroussi.github.io/yfinance/reference/api/yfinance.EquityQuery.html
- yfinance websocket: https://ranaroussi.github.io/yfinance/reference/yfinance.websocket.html
- yfinance ticker source (options columns incl. impliedVolatility): https://raw.githubusercontent.com/ranaroussi/yfinance/refs/heads/main/yfinance/ticker.py
- pandas package overview: https://pandas.pydata.org/docs/dev/getting_started/overview.html
- SEC EDGAR API docs: https://www.sec.gov/edgar/sec-api-documentation
- SEC developer fair-access guidance: https://www.sec.gov/about/developer-resources
- Alpha Vantage API docs: https://www.alphavantage.co/documentation/
- Polygon stocks data overview: https://polygon.io/stocks
- Morningstar stock quote overview: https://www.morningstar.com/help-center/stocks/stock-quote-page
- Koyfin watchlists: https://www.koyfin.com/features/watchlists/
- Koyfin dashboards: https://www.koyfin.com/features/custom-dashboards/
- Koyfin portfolio tools: https://www.koyfin.com/features/portfolio-tools/
- Boneyard repository: https://github.com/0xGF/boneyard
- Boneyard overview: https://boneyard.vercel.app/overview
- Boneyard performance notes: https://boneyard.vercel.app/performance
- Awesome DESIGN.md repository: https://github.com/VoltAgent/awesome-design-md
- Coinbase DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/coinbase/DESIGN.md
- Revolut DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/revolut/DESIGN.md
- Sentry DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/sentry/DESIGN.md

## Open Questions

- None.
