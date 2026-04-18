## 1. Discovery and Fail-First Contracts

- [x] 1.1 Freeze a keep, move, and remove inventory for the current frontend before any archive or rebuild work begins.
  Notes: Default keep scope should be limited to hierarchy pivot behavior, report lifecycle behavior, lifecycle state patterns, and reusable typed finance formatting/utilities. Frozen inventory matrix: `docs/product/compact-dashboard-discovery-baseline.md` (Section 1).

- [x] 1.2 Add fail-first frontend contract tests for the compact dashboard shell: bounded first viewport, route-specific progressive disclosure, and non-scroll-first decision visibility.
  Notes: Treat deep vertical stacking as a contract failure on the home route and keep route boundaries explicit. Fail-first artifact: `frontend/src/app/compact-dashboard-shell.contract.fail-first.test.ts`.

- [x] 1.3 Add fail-first tests for explicit `unavailable` rendering when fundamental or technical research metrics lack real backend support.
  Notes: No placeholder numbers or silent omissions. Fail-first artifact: `frontend/src/app/unavailable-research-metrics.contract.fail-first.test.ts`.

- [x] 1.4 Produce a yfinance metric-availability matrix for all first-surface dashboard metrics (`direct`, `derived`, `unavailable`).
  Notes: This matrix must be sourced from official yfinance docs/source and becomes the implementation baseline for the `Opportunities` surface within `/portfolio/signals`. Matrix artifact: `docs/product/compact-dashboard-discovery-baseline.md` (Section 2).

- [x] 1.5 Produce a UX contract matrix from `boneyard` + `awesome-design-md` references for loading states, spacing rhythm, corner tokens, and storytelling flow.
  Notes: Output must be implementation-ready (`token`, `rule`, `applies_to`, `mobile_adjustment`) and aligned to the five-route dashboard constraints. Matrix artifact: `docs/product/compact-dashboard-discovery-baseline.md` (Section 3).

## 2. Legacy Archive and New Frontend Foundation

- [x] 2.1 Archive the current frontend into repo-root `/v0` before replacing the active app.
  Notes: Prefer `v0/frontend-legacy/` plus a short archive manifest over leaving the old app mixed into the new tree. Archive evidence: `v0/frontend-legacy/ARCHIVE_MANIFEST.md`.

- [x] 2.2 Scaffold a clean active `frontend/` foundation with only the minimum shell, routing, theming, typed API client, and lifecycle-state primitives required for the redesign.
  Notes: The shell must support the five route surfaces plus compact utility actions without reintroducing a route-heavy workspace. Foundation artifacts: `frontend/src/{app/{App.tsx,router.tsx,styles.css,providers.tsx,theme.tsx},components/shell/CompactDashboardShell.tsx,features/report-utility/ReportUtilityDock.tsx,pages/portfolio-*-page/*.tsx}`.

- [x] 2.3 Re-import only the reusable current assets that still pay rent in the compact design.
  Notes: Good candidates include finance-safe formatting, selected Zod schemas, provenance copy, and preserved table/report state primitives. Re-imported assets: `frontend/src/core/lib/{decimal.ts,formatters.ts,dates.ts,provenance.ts}`, `frontend/src/core/api/{client.ts,errors.ts,schemas.ts}`, `frontend/src/core/config/env.ts`, `frontend/src/features/portfolio-workspace/state-copy.ts`, `frontend/src/components/workspace-layout/WorkspaceStateBanner.tsx`.

## 3. Compact Dashboard Information Architecture

- [x] 3.1 Implement one compact primary dashboard shell with five routes: `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, and `/portfolio/asset-detail/:ticker`.
  Notes: Reject any implementation that reintroduces a route-heavy workspace or mixes executive, interpretive, tactical, and deep-dive jobs on the same surface.
  Implementation: Shell now enforces five-route navigation plus a route-question decision-journey rail with one primary job per route. Artifacts: `frontend/src/components/shell/CompactDashboardShell.tsx`, `frontend/src/app/compact-dashboard-information-architecture.contract.test.tsx`.

- [x] 3.2 Build `/portfolio/home` as the default landing route to answer: how is my portfolio doing right now, how am I doing vs benchmark, and what needs attention immediately.
  Implementation: Added executive home first viewport with KPI strip, benchmark spread, immediate-attention module (`Action state: wait`), plus bounded secondary allocation/top-movers/holdings blocks. Artifacts: `frontend/src/pages/portfolio-home-page/PortfolioHomePage.tsx`, `frontend/src/pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx`.

- [x] 3.3 Build `/portfolio/analytics` to answer: why did the portfolio move, which assets drove the result, and is performance consistent.
  Implementation: Added explainability first viewport with performance curve, attribution drivers, consistency module, and bounded advanced disclosure for deeper decomposition. Artifacts: `frontend/src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx`, `frontend/src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx`.

- [x] 3.4 Build `/portfolio/risk` to answer: how fragile is the portfolio, where is concentration hidden, and what is the risk profile.
  Implementation: Added risk first-viewport triage modules (`Fragility snapshot`, `Hidden concentration`, `Risk profile`) plus bounded advanced diagnostics disclosure. Artifacts: `frontend/src/pages/portfolio-risk-page/PortfolioRiskPage.tsx`, `frontend/src/pages/portfolio-risk-page/PortfolioRiskPage.contract.test.tsx`.

- [x] 3.5 Build `/portfolio/signals` as the secondary tactical overlay for ranked review, signal state, and watchlist candidates.
  Implementation: Added secondary tactical overlay modules (`Ranked review queue`, `Signal state overview`, `Watchlist candidates`) while preserving explicit unavailable-state contract copy and availability matrix rendering. Artifacts: `frontend/src/pages/portfolio-signals-page/PortfolioSignalsPage.tsx`, `frontend/src/pages/portfolio-signals-page/PortfolioSignalsPage.contract.test.tsx`.

- [x] 3.6 Build `/portfolio/asset-detail/:ticker` as the deep dive for per-asset context, with candlesticks isolated to this route.
  Implementation: Added ticker-level deep-dive modules (`Candlestick price action`, `Price-volume context`, `Per-asset risk profile`) and contract coverage that enforces candlestick isolation from executive routes. Artifacts: `frontend/src/pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx`, `frontend/src/pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.contract.test.tsx`.

- [x] 3.7 Reintroduce the preserved hierarchy pivot behavior and compact report utility inside bounded disclosures of the new shell.
  Notes: Preserve grouped-row expand/collapse behavior in holdings/position detail tables and keep report generation/export as a compact utility, not a standalone route.
  Implementation: Added reusable grouped-row hierarchy pivot table with expand/collapse controls and re-wired holdings/position-detail as bounded disclosures; compact report utility is now disclosure-bound in the shell (no standalone route). Artifacts: `frontend/src/{features/portfolio-hierarchy/HierarchyPivotTable.tsx,components/shell/CompactDashboardShell.tsx,pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx},app/compact-preserved-behaviors.contract.test.tsx}`.

- [x] 3.8 Implement module storytelling contracts (`what`, `why`, `action`, `evidence`) for all primary blocks across the five routes.
  Notes: This is a required UX behavior, not optional copy polish.
  Implementation: Added reusable storytelling contract block (`What/Why/Action/Evidence`) and applied it across primary modules on `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, and `/portfolio/asset-detail/:ticker`. Artifacts: `frontend/src/{components/storytelling/StoryContractBlock.tsx,pages/portfolio-*-page/*.tsx,app/module-storytelling.contract.test.tsx}`.

- [x] 3.9 Implement a phi-derived layout token scale (`1.613`) for spacing, module heights, and rhythm constraints.
  Notes: Preserve readability and accessibility over strict numeric purity; avoid forcing phi where it harms density or scanability.
  Implementation: Added explicit phi-derived token set (`--phi-ratio: 1.613`, spacing `8/13/21/34/55`, module heights `233/377/610`) and wired rhythm/min-height usage with mobile overrides to preserve readability. Artifacts: `frontend/src/app/styles.css`, `frontend/src/app/phi-layout-scale.contract.test.ts`.

## 4. Research and Risk Modules

- [x] 4.1 Implement the `/portfolio/home` executive surface with KPI strip, equity curve, attention panel, top movers, allocation snapshot, and holdings summary table.
  Notes: Keep this route clean and selective; it is the default state and attention surface.
  Implementation: Rebuilt the home executive modules into explicit `equity curve vs benchmark`, `needs attention immediately`, `top movers`, `allocation snapshot`, and `holdings summary table` surfaces while preserving hierarchy-pivot behavior in bounded disclosure. Artifacts: `frontend/src/pages/portfolio-home-page/{PortfolioHomePage.tsx,PortfolioHomePage.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.2 Implement the `/portfolio/analytics` explainability surface with performance curve, attribution waterfall, contribution leaders, monthly heatmap, rolling return chart, and drill-down table.
  Notes: Each visual must answer a unique explanation question; do not repeat attribution in multiple forms.
  Implementation: Reworked analytics into six explicit explainability modules (`performance curve`, `attribution waterfall`, `contribution leaders`, `monthly return heatmap`, `rolling return chart`, `drill-down contribution table`) with bounded secondary evidence panels. Artifacts: `frontend/src/pages/portfolio-analytics-page/{PortfolioAnalyticsPage.tsx,PortfolioAnalyticsPage.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.3 Implement the `/portfolio/risk` fragility surface with risk posture, drawdown timeline, return distribution, risk/return scatter, correlation heatmap, and concentration table.
  Notes: Advanced diagnostics remain available but must not crowd the main risk triage surface.
  Implementation: Reworked risk into six explicit fragility modules (`risk posture`, `drawdown timeline`, `return distribution`, `risk/return scatter`, `correlation heatmap`, `concentration table`) while keeping advanced diagnostics in bounded disclosure and preserving explicit action-state messaging. Artifacts: `frontend/src/pages/portfolio-risk-page/{PortfolioRiskPage.tsx,PortfolioRiskPage.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.4 Implement the `/portfolio/signals` tactical review surface with trend regime summary, momentum ranking, technical signals table, and watchlist panel.
  Notes: Keep tactical review secondary and summarized, not terminal-like.
  Implementation: Reworked `/portfolio/signals` into explicit tactical modules (`trend regime summary`, `momentum ranking`, `technical signals table`, `watchlist panel`) with module-level contract state, bounded unavailable handling, and retained secondary-route posture. Artifacts: `frontend/src/pages/portfolio-signals-page/{PortfolioSignalsPage.tsx,PortfolioSignalsPage.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.5 Implement the `/portfolio/asset-detail/:ticker` deep dive with asset hero, price action, price-volume combo, position detail, benchmark-relative chart, asset risk metrics, and narrative notes.
  Notes: Candlestick treatment is restricted to this route only.
  Implementation: Expanded `/portfolio/asset-detail/:ticker` into seven deep-dive modules (`asset hero`, `price action`, `price-volume combo`, `position detail`, `benchmark-relative chart`, `asset risk metrics`, `narrative notes`) while preserving candlestick isolation to asset-detail. Artifacts: `frontend/src/pages/portfolio-asset-detail-page/{PortfolioAssetDetailPage.tsx,PortfolioAssetDetailPage.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.6 Define and implement source contracts for market prices, fundamentals, reference metadata, and derived signals.
  Notes: `pandas` is transformation-only; yfinance is primary source in this phase; every surfaced metric must expose provenance (`source_id`, `as_of`, `freshness_state`, `confidence_state`).
  Implementation: Added typed source-contract primitives and health evaluation (`market_prices`, `fundamentals`, `reference_metadata`, `derived_signals`) plus route integration that renders explicit provenance fields (`source_id`, `as_of`, `freshness_state`, `confidence_state`). Artifacts: `frontend/src/features/portfolio-workspace/source-contracts.ts`, `frontend/src/core/api/schemas.ts`, `frontend/src/pages/{portfolio-signals-page/PortfolioSignalsPage.tsx,portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx}`.

- [x] 4.7 Add fail-first data-quality and reliability tests for stale data, missing contracts, timezone/session mismatch, and provider failure handling.
  Notes: Blast radius control requirement is module isolation plus graceful `unavailable`, never silent substitutions.
  Implementation: Added contract tests that fail on stale-data freshness violations, missing required contracts, timezone/session mismatches, and provider failures; source-contract evaluator now degrades to explicit module states/reason codes instead of silent fallback. Artifacts: `frontend/src/features/portfolio-workspace/source-contracts.contract.test.ts`, `frontend/src/features/portfolio-workspace/source-contracts.ts`, `frontend/src/features/portfolio-workspace/state-copy.ts`.

- [x] 4.8 Add feature flags and kill-switch controls for high-risk research modules before enabling advanced decision states.
  Notes: Gate examples: `advanced_signals_enabled`, `fundamentals_contract_v1`.
  Implementation: Added typed research control flags + kill-switches (`advanced_signals_enabled`, `fundamentals_contract_v1`, `high_risk_research_modules_disabled`, `advanced_decision_states_disabled`) and wired tactical module/action-state gating for explicit downgrade behavior. Artifacts: `frontend/src/features/portfolio-workspace/{feature-flags.ts,feature-flags.contract.test.ts}`, `frontend/src/pages/{portfolio-signals-page/PortfolioSignalsPage.tsx,portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx}`, `frontend/src/core/api/schemas.ts`.

- [x] 4.9 Implement yfinance extraction adapters for first-surface valuation, quality, and technical inputs that are confirmed available now.
  Notes: Prioritize `P/E`, `PEG`, `P/B`, `ROE`, `ROA`, debt/current ratios, OHLCV, actions, and option-chain `impliedVolatility`; only mark unavailable after matrix validation.
  Implementation: Added typed yfinance extraction adapters for valuation (`P/E`, `PEG`, `P/B`), quality (`ROE`, `ROA`, debt-to-equity, current ratio), and technical inputs (OHLCV, actions, option-chain implied volatility, ATR derivation) and surfaced the extraction table in `/portfolio/signals`. Artifacts: `frontend/src/features/portfolio-workspace/{yfinance-extraction-adapters.ts,yfinance-extraction-adapters.contract.test.ts,research-metric-availability.ts}`, `frontend/src/pages/portfolio-signals-page/hooks/usePortfolioSignalsRouteState.ts`, `frontend/src/pages/portfolio-signals-page/components/PortfolioSignalsRouteView.tsx`.

- [x] 4.10 Preserve and compact the Quant report utility with scope and date controls.
  Notes: Keep `Generate HTML report` actions, add report date-range selector, and preserve explicit lifecycle states without making it a standalone route.
  Implementation: Preserved compact report utility actions with scope/date controls, explicit lifecycle transitions, validation for symbol/date range failures, reset date-range icon action, and contract coverage for lifecycle behavior. Artifacts: `frontend/src/features/report-utility/{ReportUtilityDock.tsx,ReportUtilityDock.contract.test.tsx}`, `frontend/src/app/styles.css`.

- [x] 4.11 Implement stable skeleton-loading contracts for all primary modules.
  Notes: Use fixed-height placeholders mapped to final module geometry to avoid layout jumps during loading/error retries.
  Implementation: Added fixed-height primary module skeleton primitives plus route query-state loading wiring (`module_state=loading`) across home, analytics, risk, signals, and asset-detail routes. Artifacts: `frontend/src/components/skeletons/PrimaryModuleSkeleton.tsx`, `frontend/src/features/portfolio-workspace/route-module-state.ts`, `frontend/src/pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-analytics-page/PortfolioAnalyticsPage.tsx,portfolio-risk-page/PortfolioRiskPage.tsx,portfolio-signals-page/components/PortfolioSignalsRouteView.tsx,portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx}`, `frontend/src/app/{primary-module-skeleton.contract.test.tsx,styles.css}`.

- [x] 4.12 Refactor route modules into colocated component directories with container/presentation separation where data loading or route state is non-trivial.
  Notes: Prefer composition over configuration-heavy wrappers; keep focused presentational modules small enough to review and test without route-file sprawl.
  Implementation: Refactored non-trivial route modules (`/portfolio/signals`, `/portfolio/asset-detail/:ticker`) into colocated `hooks/` + `components/` container/presentation structure with thin route entry files. Artifacts: `frontend/src/pages/portfolio-signals-page/{PortfolioSignalsPage.tsx,hooks/usePortfolioSignalsRouteState.ts,components/PortfolioSignalsRouteContainer.tsx,components/PortfolioSignalsRouteView.tsx}`, `frontend/src/pages/portfolio-asset-detail-page/{PortfolioAssetDetailPage.tsx,hooks/usePortfolioAssetDetailRouteState.ts,components/PortfolioAssetDetailRouteContainer.tsx,components/PortfolioAssetDetailRouteView.tsx}`, `frontend/src/app/route-colocation.contract.test.ts`.

- [x] 4.13 Add accessibility contract tests and implementation fixes for keyboard navigation, visible focus, semantic headings/labels, icon-button aria labels, and non-color-only state communication across all five routes.
  Notes: Treat WCAG 2.1 AA behaviors as implementation gates, not post-polish work.
  Implementation: Added accessibility contract coverage and fixes for keyboard semantics (`aria-current`, route-journey toggle button), visible focus styling (`:focus-visible` + focus ring token), icon-button aria labels (journey toggle + report date reset), and explicit non-color state cues across analytics/signals/asset-detail modules. Artifacts: `frontend/src/app/{accessibility.contract.test.tsx,styles.css}`, `frontend/src/components/shell/CompactDashboardShell.tsx`, `frontend/src/features/report-utility/ReportUtilityDock.tsx`, `frontend/src/pages/{portfolio-analytics-page/PortfolioAnalyticsPage.tsx,portfolio-signals-page/components/PortfolioSignalsRouteView.tsx,portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx}`.

- [x] 4.14 Add responsive layout contract tests and implementation fixes for `320`, `768`, `1024`, and `1440` widths, with no horizontal overflow and route-aware density adaptation.
  Notes: Validate mobile-first rendering for home, analytics, risk, signals, and asset-detail before documentation handoff.
  Implementation: Added responsive contract coverage and implementation for explicit `320/768/1024/1440` breakpoints, route-aware shell density metadata, and no-horizontal-overflow shell guard attributes. Artifacts: `frontend/src/app/{responsive-layout.contract.test.tsx,styles.css}`, `frontend/src/components/shell/CompactDashboardShell.tsx`.

- [x] 4.15 Enforce semantic design-token usage for route-level UI (`color`, `spacing`, `typography`, `border`, `radius`) and remove arbitrary raw values or AI-default styling patterns from the rebuilt surfaces.
  Notes: No raw hex-driven route styling, no off-scale spacing, no maximum-radius-everywhere cards, and no purple-first fallback palette.
  Implementation: Introduced semantic route token aliases for surface/border/spacing/radius/typography and routed shell/panel styles through those aliases while preserving non-purple palette and route-level raw color bans. Artifacts: `frontend/src/app/{semantic-token-usage.contract.test.ts,styles.css}`.

- [x] 4.16 Implement explicit empty, unavailable, retryable error, and success-feedback states for all primary modules beyond loading skeletons.
  Notes: State feedback must be meaningful, bounded to the module, and preserve layout stability.
  Implementation: Extended route module-state handling to include `empty/unavailable/success/error`, added shared primary-module feedback with retry, and wired feedback behavior across home, analytics, risk, signals, and asset-detail primary surfaces. Artifacts: `frontend/src/features/portfolio-workspace/route-module-state.ts`, `frontend/src/components/workspace-layout/PrimaryModuleStateFeedback.tsx`, `frontend/src/pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-analytics-page/PortfolioAnalyticsPage.tsx,portfolio-risk-page/PortfolioRiskPage.tsx,portfolio-signals-page/components/PortfolioSignalsRouteView.tsx,portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx}`, `frontend/src/app/primary-module-state-feedback.contract.test.tsx`.

- [x] 4.17 Codify the simplest-possible frontend state ownership model for the rebuilt shell (`local UI state`, `URL state`, `server state`) and add tests that prevent unnecessary global-store or prop-drilling regressions.
  Notes: Route filters, report controls, and shareable view state should prefer URL state; remote data should stay in typed server-state boundaries; avoid prop drilling deeper than three levels.
  Implementation: Added explicit state-ownership boundaries utility, prop-drill depth guard, and URL-backed report control persistence for shareable route views while keeping global-store dependencies out of rebuilt routes. Artifacts: `frontend/src/features/portfolio-workspace/{state-ownership.ts,state-ownership.contract.test.tsx}`, `frontend/src/features/report-utility/ReportUtilityDock.tsx`.

## 5. Documentation and Validation

- [x] 5.1 Keep `docs/product/trading-dashboard-llm-wiki.md` synchronized with the final preserve list, IA, financial framework, and third-pass refinement memo used in implementation.
  Implementation: Rewrote the trading-dashboard wiki to align with the implemented five-route IA, final preserve list, storytelling framework, and third-pass refinement priority while removing outdated two-tab guidance. Artifacts: `docs/product/trading-dashboard-llm-wiki.md`.

- [x] 5.2 Run frontend validation gates for the rebuilt app (`test`, `lint` or `type-check`, and `build`) and capture any archive-specific tooling notes.
  Implementation: Executed full frontend gates (`test`, `lint`, `build`) and captured archive-specific tooling notes (OpenSpec telemetry DNS warnings are non-blocking; frontend lint/type-check equivalence) in rebuild handoff notes. Artifacts: `docs/product/compact-trading-dashboard-implementation-handoff.md`.

- [x] 5.3 Update `CHANGELOG.md`, rerun OpenSpec validation, and prepare implementation handoff notes for the rebuild slice.
  Implementation: Added rebuild-slice implementation handoff notes and updated changelog entries for documentation/validation closeout, then reran strict OpenSpec change validation. Artifacts: `docs/product/compact-trading-dashboard-implementation-handoff.md`, `CHANGELOG.md`.

- [x] 5.4 Document source-policy decisions (yfinance-first extraction map, derivation formulas with pandas, provenance UX, explicit non-native signals, and route-specific chart grammar) in product docs and implementation handoff.
  Implementation: Documented canonical source policy decisions, yfinance-first extraction map, deterministic pandas derivation formulas, provenance UX metadata contract, explicit non-native signal handling, and route-specific chart grammar in both product wiki and handoff notes. Artifacts: `docs/product/trading-dashboard-llm-wiki.md`, `docs/product/compact-trading-dashboard-implementation-handoff.md`.
