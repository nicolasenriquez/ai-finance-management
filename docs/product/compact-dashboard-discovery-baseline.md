# Compact Dashboard Discovery Baseline

Date: 2026-04-17
Change: `archive-v0-and-build-compact-trading-dashboard`
Task slice: `1.1-1.5`

This baseline freezes discovery decisions before any archive/rebuild actions in section 2+.

## 1) Preserve/Move/Remove Inventory Freeze

| Inventory ID | Current asset | Current path(s) | Decision | Archive destination (`/v0`) | Compact dashboard destination | Rationale |
| --- | --- | --- | --- | --- | --- | --- |
| `INV-KEEP-01` | Hierarchy pivot behavior (grouped rows, expand/collapse, deterministic sort) | `frontend/src/features/portfolio-hierarchy/PortfolioHierarchyTable.tsx`, `frontend/src/features/portfolio-hierarchy/PortfolioHierarchyTable.test.tsx` | `KEEP` | `v0/frontend-legacy/src/features/portfolio-hierarchy/*` | `/portfolio/home` allocation snapshot + `/portfolio/asset-detail/:ticker` position detail | Required preserve scope from task note; high decision value per interaction cost. |
| `INV-KEEP-02` | Quant report lifecycle behavior and actions (`Generate HTML report`, `Export analyst pack`) | `frontend/src/pages/portfolio-reports-page/PortfolioReportsPage.tsx`, `frontend/src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx` | `KEEP` | `v0/frontend-legacy/src/pages/portfolio-reports-page/*` | Compact utility dock (secondary disclosure), not a primary route | Preserve lifecycle reliability while reducing route-first workspace sprawl. |
| `INV-KEEP-03` | Lifecycle-state patterns (`loading`, `empty`, `stale`, `unavailable`, `error`) | `frontend/src/features/portfolio-workspace/state-copy.ts`, `frontend/src/components/workspace-layout/WorkspaceStateBanner.tsx` | `KEEP` | `v0/frontend-legacy/src/features/portfolio-workspace/state-copy.ts`, `v0/frontend-legacy/src/components/workspace-layout/WorkspaceStateBanner.tsx` | Shared route primitives across all five compact routes | Explicit state handling is mandatory for fail-fast trust semantics. |
| `INV-KEEP-04` | Typed finance-safe formatting/utilities | `frontend/src/core/lib/formatters.ts`, `frontend/src/core/lib/dates.ts`, `frontend/src/core/lib/provenance.ts` | `KEEP` | `v0/frontend-legacy/src/core/lib/*` | Shared utility layer in active compact shell | Prevents silent precision drift and inconsistent money/date rendering. |
| `INV-MOVE-01` | Attribution waterfall | `frontend/src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx` | `MOVE` | `v0/frontend-legacy/src/pages/portfolio-analytics-page/*` | `/portfolio/analytics` advanced disclosure block | Valuable but secondary to first-view contribution interpretation. |
| `INV-MOVE-02` | Rolling risk, correlation, and tail diagnostics | `frontend/src/pages/portfolio-risk-page/PortfolioRiskPage.tsx` | `MOVE` | `v0/frontend-legacy/src/pages/portfolio-risk-page/*` | `/portfolio/risk` advanced disclosure block | Keep risk triage first; move dense diagnostics behind bounded disclosure. |
| `INV-MOVE-03` | Report lifecycle as full route | `frontend/src/pages/portfolio-reports-page/PortfolioReportsPage.tsx` | `MOVE` | `v0/frontend-legacy/src/pages/portfolio-reports-page/*` | Compact report utility available from `/portfolio/home` and `/portfolio/asset-detail/:ticker` | Preserve behavior, remove route overhead. |
| `INV-REMOVE-01` | Legacy route-heavy first surface (`dashboard`, `holdings`, `performance`, `rebalancing`, `transactions` as primary navigation spine) | `frontend/src/app/router.tsx`, `frontend/src/features/portfolio-workspace/dashboard-governance.ts` | `REMOVE` (as primary UX) | `v0/frontend-legacy/src/app/router.tsx` | Replace with five-route compact shell (`home`, `analytics`, `risk`, `signals`, `asset-detail/:ticker`) | Current shell violates compact-first and non-scroll-first decision goals. |
| `INV-REMOVE-02` | Any duplicate equal-priority visuals for one analytical question | Governance artifacts + route pages | `REMOVE` | Preserved only in archive for audit context | Enforced out of first surface by compact governance/tests | Duplicate first-surface visuals weaken clarity and decision speed. |

## 2) YFinance Metric Availability Matrix (First-Surface Metrics)

Legend:
- `direct`: available from yfinance endpoint/field directly.
- `derived`: computed deterministically from yfinance direct data.
- `unavailable`: no supported direct contract in current baseline; render explicit unavailable state.

| Route | First-surface metric intent | yfinance extraction path | Status | Implementation baseline note |
| --- | --- | --- | --- | --- |
| `/portfolio/home` | Price level and daily move | `Ticker.history` or `download` OHLCV | `direct` | Canonical first-view market movement context. |
| `/portfolio/home` | Benchmark-relative trend line | `download` for benchmark symbol + portfolio series | `direct` | Keep benchmark comparison explicit in same frame. |
| `/portfolio/home` | Top movers ranking | latest close and period return from OHLCV | `derived` | Rank by deterministic return/change formula from direct prices. |
| `/portfolio/home` | Dividend activity context | `Ticker.dividends` / `Ticker.actions` | `direct` | Show payout evidence with as-of metadata. |
| `/portfolio/analytics` | Rolling return consistency | OHLCV return windows (30D/90D/252D) | `derived` | Derived from direct closes; no synthetic rows. |
| `/portfolio/analytics` | Monthly return heatmap | OHLCV resampled monthly returns | `derived` | Deterministic resample formula (pandas). |
| `/portfolio/risk` | Drawdown path | close series -> running max drawdown | `derived` | Derived risk baseline from direct price history. |
| `/portfolio/risk` | Return distribution buckets | close-to-close returns histogram | `derived` | Explicit bin policy in UI metadata. |
| `/portfolio/risk` | Correlation heatmap inputs | aligned return vectors by symbol | `derived` | Derived pairwise correlation from direct OHLCV. |
| `/portfolio/signals` | P/E | `EquityQuery` field `peratio.lasttwelvemonths` (and/or `Ticker.info` fallback where available) | `direct` | Prefer screener field path for consistent extraction semantics. |
| `/portfolio/signals` | PEG | `EquityQuery` field `pegratio_5y` | `direct` | Keep provenance as direct screener field. |
| `/portfolio/signals` | P/B | `EquityQuery` field `pricebookratio.quarterly` | `direct` | Contract varies by ticker coverage; surface unavailable per symbol when missing. |
| `/portfolio/signals` | ROE | `EquityQuery` field `returnonequity.lasttwelvemonths` | `direct` | Show direct status with freshness metadata. |
| `/portfolio/signals` | ROA | `EquityQuery` field `returnonassets.lasttwelvemonths` | `direct` | Same provenance policy as ROE. |
| `/portfolio/signals` | Debt-to-equity | `EquityQuery` field `totaldebtequity.lasttwelvemonths` | `direct` | Confidence depends on symbol coverage; never fabricate value. |
| `/portfolio/signals` | Current ratio | `EquityQuery` field `currentratio.lasttwelvemonths` | `direct` | Same explicit missing-contract behavior as other fundamentals. |
| `/portfolio/signals` | 50D/200D regime | moving averages from OHLCV | `derived` | Deterministic regime rules from direct price history. |
| `/portfolio/signals` | ATR | OHLCV high/low/close -> ATR formula | `derived` | Derived technical, tagged `derived` confidence state. |
| `/portfolio/signals` | Support/resistance bands | OHLCV extrema/rolling windows | `derived` | Heuristic, deterministic derivation only. |
| `/portfolio/signals` | Option-chain implied volatility | `Ticker.option_chain(...).calls/puts.impliedVolatility` | `direct` | Contract-level IV available directly where chain exists. |
| `/portfolio/signals` | Rule of 40 | no first-class yfinance field | `unavailable` | Requires explicit custom fundamental contract before use in action guidance. |
| `/portfolio/signals` | J5 / JR4 proprietary labels | no native yfinance field | `unavailable` | Render unavailable until custom deterministic rule engine is defined. |
| `/portfolio/signals` | Historical IV percentile series | no first-class yfinance percentile endpoint | `unavailable` | Do not imply native availability without custom derivation contract. |
| `/portfolio/signals` | Green-on-green / red-on-red labels | no native yfinance label contract | `unavailable` | Explicitly non-native signals; keep blocked until custom contract exists. |
| `/portfolio/asset-detail/:ticker` | Price-volume combo | OHLCV close + volume | `direct` | Candlestick and volume pairing stays isolated to asset detail route. |
| `/portfolio/asset-detail/:ticker` | Corporate action context | `Ticker.actions`, `Ticker.splits`, `Ticker.dividends` | `direct` | Use actions as evidence path for major moves. |

Official yfinance sources used for this matrix:
- `Ticker` API reference: https://ranaroussi.github.io/yfinance/reference/api/yfinance.Ticker.html
- `download` API reference: https://ranaroussi.github.io/yfinance/reference/api/yfinance.download.html
- Financial statements reference: https://ranaroussi.github.io/yfinance/reference/yfinance.financials.html
- `EquityQuery`/screener fields reference: https://ranaroussi.github.io/yfinance/reference/api/yfinance.EquityQuery.html
- yfinance ticker source (`impliedVolatility` option-chain column): https://raw.githubusercontent.com/ranaroussi/yfinance/refs/heads/main/yfinance/ticker.py

## 3) UX Contract Matrix (`boneyard` + `awesome-design-md`)

| token | rule | applies_to | mobile_adjustment |
| --- | --- | --- | --- |
| `viewport.desktop.max-height.900` | First decision strip + hero evidence must fit within a 900px desktop viewport budget before deeper disclosures. | `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals` | Treat 640px as first-screen budget and keep only `what` + `action` visible initially. |
| `loading.skeleton.hero.377` | Hero skeleton keeps near-final geometry; no loading-to-ready layout jump. | Route hero module on all five routes | Reduce to 233px on narrow screens while preserving identical content ordering. |
| `loading.skeleton.module.233` | Standard primary module skeleton height remains fixed until ready/error/unavailable state resolves. | Primary modules across home/analytics/risk/signals | Collapse stacked modules to single-column flow; keep fixed min-height. |
| `loading.skeleton.utility.144` | Utility/supplemental modules use compact fixed-height placeholders. | Secondary utilities and compact report controls | Convert to accordion rows with fixed placeholder rows. |
| `spacing.8` | Base spacing unit for dense controls and compact table rows. | Inputs, pills, row actions, metadata chips | Keep as minimum tap-safe inset; do not go below 8px. |
| `spacing.13` | Default card-internal rhythm for primary content blocks. | KPI cards, interpretation text, status rows | Use 13px vertical stack when card width >= 320px; otherwise 8px. |
| `spacing.21` | Section gutter between primary modules inside first viewport. | First-surface module boundaries | Reduce to 13px on phones to avoid unnecessary vertical growth. |
| `spacing.34` | Route section break between first-surface block and advanced disclosure block. | Transition from first surface to advanced content | Replace with disclosure toggle + 21px gap on mobile. |
| `corner.card.13` | Dense data cards use compact corner radius; no mixed-radius card families in same route. | KPI cards, tables, chart containers | Keep 13px; do not upscale on mobile dense cards. |
| `corner.panel.21` | Hero and primary narrative panels use moderate radius distinct from dense cards. | Dominant job and hero insight modules | Keep 21px only where width >= 360px; fallback to 13px below. |
| `corner.emphasis-pill.100` | High-emphasis chips/buttons may use large rounded style for explicit action framing. | Action chips (`buy/add/wait/avoid`) and key CTA buttons | Reduce to `pill.72` equivalent when control width is constrained. |
| `corner.hero-pill.135` | Maximum pill radius reserved for single dominant route action control. | One dominant action per route hero | Disable on very small screens; use `corner.emphasis-pill.100`. |
| `story.what` | Every primary module starts with explicit current metric/state sentence. | All first-surface modules in five-route shell | Keep to one line before truncation. |
| `story.why` | Primary module includes one deterministic interpretation sentence tied to investor decision meaning. | All first-surface modules in five-route shell | Collapse into expandable helper text if width < 360px. |
| `story.action` | Primary module provides one clear next-step recommendation (`buy`, `add`, `wait`, `avoid`, `unavailable`). | All decision-driving modules | Keep always visible above fold; never hide in tooltip-only affordance. |
| `story.evidence` | Primary module exposes provenance/freshness/confidence metadata as compact evidence row. | All decision-driving modules | Collapse metadata into one inline badge group with tap-to-expand details. |
| `disclosure.advanced.default-collapsed` | Advanced diagnostics stay collapsed by default to preserve non-scroll-first decision flow. | `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals` | Default to one compact accordion with deterministic expanded state label. |

Reference anchors used for the matrix:
- Boneyard repository: https://github.com/0xGF/boneyard
- Boneyard overview: https://boneyard.vercel.app/overview
- Boneyard performance notes: https://boneyard.vercel.app/performance
- Awesome DESIGN.md repository: https://github.com/VoltAgent/awesome-design-md
- Coinbase DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/coinbase/DESIGN.md
- Revolut DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/revolut/DESIGN.md
- Sentry DESIGN.md example: https://raw.githubusercontent.com/VoltAgent/awesome-design-md/main/design-md/sentry/DESIGN.md
