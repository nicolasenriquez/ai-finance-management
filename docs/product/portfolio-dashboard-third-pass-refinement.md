# Portfolio Dashboard Third-Pass Refinement

## Purpose

This memo refines the current frontend proposal into an executive-grade portfolio intelligence dashboard.
It is the implementation-facing refinement layer for the new frontend, based on:

- the existing OpenSpec proposal and current frontend direction
- the user's financial storytelling constraints
- Power BI / Tableau dashboard composition principles
- `boneyard` loading-skeleton discipline
- `awesome-design-md` spacing, hierarchy, and typography references
- `py4fi2nd` as analytical substrate inspiration only

## What Changes In This Pass

- Reduce visual redundancy.
- Compress quant depth into executive clarity.
- Treat storytelling as a first-class UI requirement.
- Separate overview, explainability, risk, tactical review, and instrument detail.
- Keep report/export actions, but collapse them into a compact utility instead of a primary route.
- Remove dashboard clutter that repeats the same insight in multiple forms.

## Product Shape

The frontend should read as a premium personal portfolio intelligence platform for a long-term investor with a secondary tactical layer.

It is not:

- a day-trading terminal
- a research notebook
- a chart gallery
- a kitchen-sink BI workspace

## Executive Route Architecture

The refined implementation should center on these 5 routes:

1. `/portfolio/home`
2. `/portfolio/analytics`
3. `/portfolio/risk`
4. `/portfolio/signals`
5. `/portfolio/asset-detail/:ticker`

All other prior surfaces should be treated as:

- secondary drill-downs
- compact utilities
- or legacy behaviors to preserve only if they still pay rent

## Route Blueprint

### 1. `/portfolio/home`

Role:

- executive command center

Must answer:

- how is my portfolio doing right now?
- how am I doing vs benchmark?
- what needs attention immediately?

Primary modules:

- `KpiStrip`
- `EquityCurveChart`
- `AttentionPanel`
- `TopMoversChart`
- `AllocationSnapshot`
- `HoldingsSummaryTable`

Design rule:

- this is the cleanest page
- do not put quant-lab density here
- keep report/export actions as a compact lower utility dock or overflow action, not a primary route

Above the fold:

- KPI strip
- equity curve
- attention panel
- top movers

Below the fold:

- allocation snapshot
- holdings summary table
- compact report utility

### 2. `/portfolio/analytics`

Role:

- performance explainability

Must answer:

- why did the portfolio move?
- which assets drove the result?
- is performance consistent?

Primary modules:

- `PerformanceCurve`
- `AttributionWaterfall`
- `ContributionLeadersChart`
- `MonthlyReturnsHeatmap`
- `RollingReturnChart`
- `PerformanceDrilldownTable`

Design rule:

- one chart per analytical question
- avoid repeating contribution information in both bars and tables unless the table is the exact drill-down

### 3. `/portfolio/risk`

Role:

- downside control and fragility visibility

Must answer:

- how fragile is the portfolio?
- where is concentration hidden?
- what is the risk profile?

Primary modules:

- `RiskPostureCard`
- `DrawdownTimeline`
- `ReturnDistribution`
- `RiskReturnScatter`
- `CorrelationHeatmap`
- `ConcentrationExposureTable`

Design rule:

- use area for drawdown depth/duration
- use histogram for return distribution
- use scatter for risk vs return
- use heatmap for correlation
- keep advanced diagnostics behind disclosure, not on the main risk triage surface

### 4. `/portfolio/signals`

Visible label:

- `Opportunities`

Role:

- secondary tactical overlay for opportunity discovery and review

Must answer:

- which assets deserve tactical review?
- which opportunities are active?
- where should the user look next?

Primary modules:

- `TrendRegimeSummary`
- `MomentumRanking`
- `TechnicalSignalsTable`
- `WatchlistPanel`

Design rule:

- this route is secondary
- the page can be branded `Opportunities` in the visible header while keeping the route slug `/portfolio/signals`
- do not let it redefine the product as a trader terminal
- keep technical visuals controlled and summarized

### 5. `/portfolio/asset-detail/:ticker`

Role:

- deep dive per instrument

Must answer:

- what is happening with this asset?
- how does it behave vs benchmark?
- what does the technical + portfolio context say?

Primary modules:

- `AssetHeroPanel`
- `PriceActionChart`
- `PriceVolumeComboChart`
- `PositionDetailTable`
- `BenchmarkRelativeChart`
- `AssetRiskMetrics`
- `AiNarrativeNotes`

Design rule:

- candlesticks belong here, not in the executive overview
- this is the only route where tactical price-action detail should be dominant

## Visual Grammar

Use these mappings consistently:

- time-series evolution -> line chart
- drawdown depth/duration -> area chart
- ranking/comparison -> ordered horizontal bars
- bridge/attribution -> waterfall
- two-variable relationship -> scatter
- cross-categorical intensity -> heatmap/highlight table
- OHLC price action -> candlestick only in asset detail
- exactness/auditability -> compact table or matrix
- related metrics on same timeline -> combo chart
- state/regime/score -> KPI card + badge/tag

## What To Remove Or Demote

Remove or demote visuals that repeat the same answer:

- donut charts for complex allocation
- gauges
- radar charts
- 3D charts
- decorative chart variety
- repeated metric displays in chart + table + card
- treemaps as primary decision visuals
- notebook-like chart walls
- long vertical scroll stacks
- tactical visuals in the main executive overview

## Storytelling Sequence

The user journey should follow:

1. current portfolio state
2. explanation of movement
3. downside and concentration risk
4. tactical review opportunities
5. asset-level deep dive

This sequence should drive:

- route order
- page hierarchy
- component prominence
- drill-down flow
- filter placement

## Quant Substrate Guidance

Use advanced finance/quant repositories like `py4fi2nd` as inspiration for the analytical substrate only.

Extract:

- time-series thinking
- performance/risk/statistics discipline
- signal readiness
- monitoring logic
- modeling rigor

Do not copy:

- notebook presentation
- research-lab density
- visible calibration clutter
- quant-first navigation

Quant depth must be compressed into executive clarity.

## Loading And Skeleton Strategy

Use `boneyard`-style stable skeletons:

- fixed geometry
- no layout jumps
- loading states that mirror final information hierarchy
- compact placeholders that reserve space for ready-state content

## Information Distribution Rules

### Home

Above the fold:

- KPI strip
- equity curve
- attention panel
- top movers

Below the fold:

- allocation snapshot
- holdings summary table
- compact export/report utility

### Analytics

Above the fold:

- performance curve
- attribution waterfall

Below the fold:

- monthly heatmap
- rolling return chart
- drill-down table

### Risk

Above the fold:

- risk posture
- drawdown timeline

Below the fold:

- return distribution
- scatter
- correlation heatmap
- concentration table

### Signals

Keep compact:

- summary first
- ranked list second
- table detail third

### Asset Detail

Above the fold:

- asset hero
- price action
- price-volume combo

Below the fold:

- benchmark relative view
- position detail
- risk metrics
- narrative notes

## Implementation Steering

Build first:

1. route shell and navigation contract
2. shared panel primitives
3. KPI strip
4. attention panel
5. chart card / table card anatomy
6. loading skeleton system

Then:

1. home route
2. analytics route
3. risk route
4. signals route
5. asset detail route

Keep reusable shared components small and typed:

- `RouteFrame`
- `KpiStrip`
- `ChartPanel`
- `InsightPanel`
- `CompactUtilityDock`
- `DataTablePanel`
- `StateBadge`
- `LoadingSkeleton`

## Data Contract Expectations

Each visible metric should carry:

- value
- unit
- comparison frame
- trend direction
- source id
- as-of timestamp
- freshness state
- confidence state

Do not surface unsupported metrics as if they were authoritative.

## Use This Refinement To Simplify

If a component does not improve decision-making, remove it.

If two visuals explain the same idea, keep one.

If a route cannot answer its question in the first screenful, restructure it.
