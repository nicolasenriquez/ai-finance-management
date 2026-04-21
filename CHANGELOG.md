# Changelog

All notable changes to this repository are documented here.

This changelog is designed for both human readers and AI agents.
Entries must remain concise, factual, and structured.

## Entry Format

Use this structure for new entries:

```md
## YYYY-MM-DD

### <type>(<scope>): <short title>
- Summary: <what changed>
- Why: <intent/business or engineering reason>
- Files: <key files/areas>
- Validation: <tests/checks run, or blocked reason>
- Notes: <optional constraints/follow-up>
```

`type` guidance: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## 2026-04-21

### docs(product-roadmap,governance): add stage-gated data-integrity steering update and active-change execution order
- Summary: Added a roadmap steering section that formalizes a stage-gated quality model (`Bronze`/`Silver Core`/`Silver Expansion`/`Gold` equivalence), explicit gate exit criteria for data integrity and non-mutation guarantees, an immediate active-change sequence (`phase-k` before `phase-o`), and a status-alignment rule tying operational truth to OpenSpec plus changelog evidence.
- Why: Keep roadmap execution aligned with deterministic system-of-record priorities and reduce governance drift between roadmap text, active OpenSpec changes, and delivery evidence.
- Files: `docs/product/roadmap.md`, `CHANGELOG.md`.
- Validation: `rtk sed -n '1,110p' docs/product/roadmap.md` (steering content and placement verified), `rtk openspec list --json` (active-change dependency context verified).
- Notes: The steering update preserves the existing repository domain model (`pdf -> canonical -> ledger -> market_data -> analytics/ml/copilot`) and does not introduce Bronze/Silver/Gold table renaming.

## 2026-04-18

### feat(frontend-dashboard,openspec): complete phase-p compact-dashboard SaaS hardening before DCA
- Summary: Completed `phase-p-dashboard-saas-hardening-before-dca` with route-level orchestration hardening, lazy route loading + navigation prefetch, contract-backed first-surface charts on Home/Analytics/Risk, opportunities-route tactical realism upgrades, async-state normalization, and cross-route readability/accessibility regression coverage.
- Why: Finalize dashboard quality/performance hardening before starting DCA implementation so next-phase policy and decision flows build on a stable, trustworthy, and contract-backed UI surface.
- Files: `frontend/src/{app/{providers.tsx,router.tsx,styles.css,module-storytelling.contract.test.tsx},components/shell/CompactDashboardShell.tsx,pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-analytics-page/{PortfolioAnalyticsPage.tsx,hooks/usePortfolioAnalyticsRouteData.ts},portfolio-risk-page/{PortfolioRiskPage.tsx,hooks/usePortfolioRiskRouteData.ts},portfolio-signals-page/{PortfolioSignalsPage.contract.test.tsx,components/PortfolioSignalsRouteView.tsx,hooks/usePortfolioSignalsRouteState.ts}}`, `docs/product/{phase-p-dashboard-baseline-evidence.md,phase-p-dashboard-implementation-handoff.md}`, `openspec/changes/phase-p-dashboard-saas-hardening-before-dca/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test` (25 passed files / 50 passed tests), `rtk npm --prefix frontend run lint` (pass), `rtk npm --prefix frontend run build` (pass), `rtk openspec validate phase-p-dashboard-saas-hardening-before-dca --type change --strict --json` (valid), `rtk openspec validate --specs --all --json` (33/33 valid).
- Notes: Recharts emits non-blocking JSDOM container-size warnings during test runs; app build/runtime behavior remains green. DCA implementation is explicitly sequenced next and was not introduced in this phase.

### feat(portfolio-ml,docs): implement deterministic technical strategy extension for ML signals
- Summary: Extended deterministic signal generation to include daily return, SMA/EMA distance and 50/200 spread regime metrics, Bollinger `%B`, Ichimoku bias (close-proxy), monthly return metrics, and trailing 12-month return while preserving existing stable v1 signal IDs.
- Why: Move ETF notebook strategy concepts into a production-safe, deterministic backend contract that can be consumed by the current read-only portfolio ML surface.
- Files: `app/portfolio_ml/service.py`, `app/portfolio_ml/tests/test_deterministic_signal_payload_fail_first.py`, `docs/guides/portfolio-ml-technical-strategy-guide.md`, `docs/guides/portfolio-ml-phase-i-guide.md`, `docs/README.md`, `CHANGELOG.md`.
- Validation: `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run ruff check app/portfolio_ml/service.py app/portfolio_ml/tests/test_deterministic_signal_payload_fail_first.py` (pass), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run pytest -v app/portfolio_ml/tests/test_deterministic_signal_payload_fail_first.py` (2 passed), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run mypy app/portfolio_ml/service.py` (pass), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run pyright app/portfolio_ml/service.py` (0 errors).
- Notes: Ichimoku is intentionally implemented as a close-only proxy because current `series_points` payload does not include explicit daily high/low fields.

## 2026-04-18

### fix(frontend-shell,frontend-utility,frontend-contracts): remove hardcoded AAPL fallback from runtime surfaces
- Summary: Replaced the shell's asset-detail shortcut from `/portfolio/asset-detail/AAPL` to the portfolio-owned MSFT route, removed the AAPL placeholder from the report utility symbol field, and aligned the accessibility contract test with the current deep-dive example.
- Why: The runtime UI was leaking a ticker the current portfolio does not hold, which made the asset-detail affordance look disconnected from the portfolio data shown elsewhere in the app.
- Files: `frontend/src/components/shell/CompactDashboardShell.tsx`, `frontend/src/features/report-utility/ReportUtilityDock.tsx`, `frontend/src/app/accessibility.contract.test.tsx`, `CHANGELOG.md`.
- Validation: `rtk rg -n "AAPL" frontend/src --glob '!**/*.test.*' --glob '!**/*.contract.*'` returned no runtime hits after the patch.
- Notes: The asset-detail shell shortcut still uses a fixed fallback symbol until a portfolio-driven selected-ticker state is wired into the shell.

## 2026-04-18

### feat(frontend-responsive,frontend-state,openspec): execute compact-dashboard implementation slice `4.14-4.17`
- Summary: Implemented route-aware responsive shell density metadata and explicit `320/768/1024/1440` media contracts, added semantic route token aliases for surface/border/spacing/radius/typography, introduced explicit `empty/unavailable/success/error` primary-module feedback with retry-to-ready behavior, and codified simple frontend state ownership boundaries with URL-backed report controls for shareable views.
- Why: Tasks `4.14-4.17` require responsive/mobile contract hardening, semantic styling discipline, bounded module-state feedback beyond loading skeletons, and explicit local/URL/server state ownership without introducing global stores.
- Files: `frontend/src/{app/styles.css,components/shell/CompactDashboardShell.tsx,components/workspace-layout/PrimaryModuleStateFeedback.tsx,features/portfolio-workspace/{route-module-state.ts,state-ownership.ts,state-ownership.contract.test.tsx},features/report-utility/ReportUtilityDock.tsx,pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-analytics-page/PortfolioAnalyticsPage.tsx,portfolio-risk-page/PortfolioRiskPage.tsx,portfolio-signals-page/components/PortfolioSignalsRouteView.tsx,portfolio-asset-detail-page/components/PortfolioAssetDetailRouteView.tsx},app/{responsive-layout.contract.test.tsx,semantic-token-usage.contract.test.ts,primary-module-state-feedback.contract.test.tsx}}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/app/responsive-layout.contract.test.tsx src/app/semantic-token-usage.contract.test.ts src/app/primary-module-state-feedback.contract.test.tsx src/features/portfolio-workspace/state-ownership.contract.test.tsx src/features/report-utility/ReportUtilityDock.contract.test.tsx` (13 passed), `rtk npm --prefix frontend run test` (23 files / 47 tests passed), `rtk npm --prefix frontend run type-check` (pass).
- Notes: Report utility control state now prefers URL search params when rendered inside Router and falls back to local state for standalone component tests/usages.

### docs(frontend-docs,openspec): complete compact-dashboard documentation and validation slice `5.1-5.4`
- Summary: Rewrote the trading-dashboard LLM wiki to match the delivered five-route compact IA and preserve list, added rebuild implementation handoff notes with final source-policy decisions and route chart grammar, and completed documentation/validation closeout for the change.
- Why: Tasks `5.1-5.4` require canonical product-doc synchronization, explicit source-policy publication, validation evidence capture, and handoff readiness before archive.
- Files: `docs/product/{trading-dashboard-llm-wiki.md,compact-trading-dashboard-implementation-handoff.md}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test` (23 files / 47 tests passed), `rtk npm --prefix frontend run lint` (pass), `rtk npm --prefix frontend run build` (pass), `rtk openspec validate "archive-v0-and-build-compact-trading-dashboard" --type change --strict --json` (valid: true), `rtk openspec instructions apply --change "archive-v0-and-build-compact-trading-dashboard" --json` (`state: all_done`, `38/38` complete).
- Notes: OpenSpec telemetry DNS errors to `edge.openspec.dev` remain non-blocking in this environment; command outputs for validation/progress remain authoritative.

## 2026-04-17

### feat(frontend-hierarchy,frontend-storytelling,frontend-visual-tokens,openspec): execute compact-dashboard IA slice `3.7-3.9`
- Summary: Reintroduced grouped-row hierarchy pivot behavior for holdings and asset position detail via expand/collapse pivot tables, moved compact report utility into bounded shell disclosure, implemented reusable `what/why/action/evidence` storytelling contracts across all five primary routes, and codified a phi-derived layout scale (`1.613`) for spacing/module rhythm tokens.
- Why: Section `3.7-3.9` requires preserve-list behavior recovery, deterministic storytelling grammar, and consistent layout rhythm before deeper research-module implementation.
- Files: `frontend/src/{features/portfolio-hierarchy/HierarchyPivotTable.tsx,components/storytelling/StoryContractBlock.tsx,components/shell/CompactDashboardShell.tsx,pages/{portfolio-home-page/PortfolioHomePage.tsx,portfolio-analytics-page/PortfolioAnalyticsPage.tsx,portfolio-risk-page/PortfolioRiskPage.tsx,portfolio-signals-page/PortfolioSignalsPage.tsx,portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx},app/{styles.css,compact-preserved-behaviors.contract.test.tsx,module-storytelling.contract.test.tsx,phi-layout-scale.contract.test.ts}}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/app/compact-preserved-behaviors.contract.test.tsx src/app/module-storytelling.contract.test.tsx src/app/phi-layout-scale.contract.test.ts src/pages/portfolio-risk-page/PortfolioRiskPage.contract.test.tsx src/pages/portfolio-signals-page/PortfolioSignalsPage.contract.test.tsx src/pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.contract.test.tsx src/app/compact-dashboard-information-architecture.contract.test.tsx src/pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx src/app/compact-dashboard-shell.contract.fail-first.test.ts src/app/unavailable-research-metrics.contract.fail-first.test.ts src/pages/portfolio-signals-page/PortfolioSignalsPage.test.tsx` (18 passed), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass).
- Notes: Storytelling contracts are now enforced via a dedicated route-spanning contract test and hierarchy/report utility behaviors are bounded by disclosure instead of route sprawl.

### feat(frontend-risk,frontend-signals,frontend-asset-detail,openspec): execute compact-dashboard IA slice `3.4-3.6`
- Summary: Implemented the remaining IA route foundations by building `/portfolio/risk` around fragility/concentration/risk-profile triage, `/portfolio/signals` as a secondary tactical overlay with ranked review and watchlist candidates, and `/portfolio/asset-detail/:ticker` as ticker-level deep dive with isolated candlestick and price-volume treatment.
- Why: Section `3.4-3.6` requires route-purpose separation across risk triage, tactical opportunity review, and instrument-level technical context without leaking deep-dive behavior back into executive routes.
- Files: `frontend/src/{pages/portfolio-risk-page/PortfolioRiskPage.tsx,pages/portfolio-signals-page/PortfolioSignalsPage.tsx,pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.tsx,app/styles.css,pages/portfolio-risk-page/PortfolioRiskPage.contract.test.tsx,pages/portfolio-signals-page/PortfolioSignalsPage.contract.test.tsx,pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.contract.test.tsx}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/pages/portfolio-risk-page/PortfolioRiskPage.contract.test.tsx src/pages/portfolio-signals-page/PortfolioSignalsPage.contract.test.tsx src/pages/portfolio-asset-detail-page/PortfolioAssetDetailPage.contract.test.tsx src/app/compact-dashboard-information-architecture.contract.test.tsx src/pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx src/app/compact-dashboard-shell.contract.fail-first.test.ts src/app/unavailable-research-metrics.contract.fail-first.test.ts src/pages/portfolio-signals-page/PortfolioSignalsPage.test.tsx` (14 passed), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass).
- Notes: Asset-detail contracts now explicitly enforce candlestick isolation from `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, and `/portfolio/signals`.

### feat(frontend-shell,frontend-home,frontend-analytics,openspec): execute compact-dashboard IA slice `3.1-3.3`
- Summary: Implemented the compact information-architecture slice by upgrading the shell to a five-route decision-journey rail and building executable first-viewport route contracts for `/portfolio/home` (state vs benchmark vs immediate attention) and `/portfolio/analytics` (movement explanation, attribution drivers, consistency).
- Why: Section `3.1-3.3` requires one compact primary shell with strict route jobs and didactic first-surface answers before deeper risk/signals/asset-detail modules.
- Files: `frontend/src/{components/shell/CompactDashboardShell.tsx,pages/portfolio-home-page/PortfolioHomePage.tsx,pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx,app/styles.css,app/compact-dashboard-information-architecture.contract.test.tsx,pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx,pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/app/compact-dashboard-information-architecture.contract.test.tsx src/pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx src/app/compact-dashboard-shell.contract.fail-first.test.ts src/app/unavailable-research-metrics.contract.fail-first.test.ts src/pages/portfolio-signals-page/PortfolioSignalsPage.test.tsx` (10 passed), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass).
- Notes: New route-level contracts are intentionally UI-contract focused and keep advanced analytics decomposition behind collapsed disclosure by default.

### feat(frontend-archive,frontend-foundation,openspec): execute compact-dashboard archive and clean foundation slice `2.1-2.3`
- Summary: Archived the full pre-reset frontend into `v0/frontend-legacy` with an explicit manifest, replaced active `frontend/src` with a clean five-route compact-shell scaffold, and re-imported only approved reusable primitives (typed API client/env, finance-safe formatters, lifecycle copy/banner, and minimal schemas).
- Why: Section `2.x` requires a hard reset from workspace-heavy UI to a controlled compact foundation while preserving rollback safety and only carrying forward assets that still provide decision value.
- Files: `v0/frontend-legacy/**`, `v0/frontend-legacy/ARCHIVE_MANIFEST.md`, `frontend/src/{app/**,components/shell/CompactDashboardShell.tsx,components/workspace-layout/WorkspaceStateBanner.tsx,core/{api/**,config/env.ts,lib/**},features/{portfolio-workspace/{state-copy.ts,dashboard-governance.ts,research-metric-availability.ts},report-utility/ReportUtilityDock.tsx},pages/**}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass), `rtk npm --prefix frontend run test -- src/app/compact-dashboard-shell.contract.fail-first.test.ts src/app/unavailable-research-metrics.contract.fail-first.test.ts` (6 passed; compact-shell and unavailable-contract baselines now enforced on scaffold).
- Notes: Active frontend runtime caches/build artifacts were intentionally excluded from the archive (`node_modules`, `dist`, `.vite*`, `*.tsbuildinfo`) and legacy files remain recoverable under `/v0/frontend-legacy`.

### test(dashboard-discovery,openspec): execute compact-dashboard discovery slice `1.1-1.5` with fail-first shell and unavailable contracts
- Summary: Added fail-first frontend contract tests for compact-shell routing/viewport/progressive-disclosure behavior and unsupported-research `unavailable` rendering, produced a discovery baseline document with the frozen keep/move/remove inventory plus yfinance availability and UX contract matrices, and marked OpenSpec tasks `1.1-1.5` complete.
- Why: The archive/rebuild reset needs a locked discovery baseline and executable fail-first contracts before archive (`/v0`) and implementation tasks can safely proceed.
- Files: `frontend/src/app/{compact-dashboard-shell.contract.fail-first.test.ts,unavailable-research-metrics.contract.fail-first.test.ts}`, `docs/product/compact-dashboard-discovery-baseline.md`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/app/compact-dashboard-shell.contract.fail-first.test.ts src/app/unavailable-research-metrics.contract.fail-first.test.ts` (expected fail-first failures: 6 failed assertions confirming missing compact-shell/unavailable contracts in current codebase).
- Notes: Broader frontend validation is intentionally deferred until implementation tasks wire the new five-route shell and research-contract registry.

### docs(frontend-research,openspec): propose compact trading dashboard reset with `/v0` archive plan and LLM wiki
- Summary: Added a repo-native trading-dashboard wiki for LLM handoff, created an OpenSpec change proposal to archive the current frontend into `/v0`, and authored a concrete two-tab wireframe blueprint (`Opportunities` + `My Portfolio`) with viewport budgets, component IDs, endpoint mapping, scoring logic, and anti-bloat guardrails.
- Why: The current frontend surface has grown beyond the value it is delivering, and the new design direction requires a smaller, more disciplined dashboard grounded in a clear investing process instead of a tall multi-route workspace.
- Files: `docs/product/{trading-dashboard-llm-wiki.md,two-tab-dashboard-wireframe-v1.md}`, `openspec/changes/archive-v0-and-build-compact-trading-dashboard/{proposal.md,design.md,tasks.md,specs/frontend-legacy-archive/spec.md,specs/frontend-compact-trading-dashboard/spec.md,specs/frontend-dashboard-visual-system/spec.md}`, `CHANGELOG.md`.
- Validation: Documentation and artifact review against current repo state, existing `phase-n` dashboard artifacts, product docs, skill guidance, and user-provided visual/finance references. OpenSpec CLI showed inconsistent status behavior immediately after scaffold creation in this sandbox, so change consumption should be rechecked before implementation.
- Notes: This proposal intentionally avoids modifying the active dirty frontend worktree and keeps the redesign isolated to new planning artifacts.

### docs(frontend-research,openspec): harden compact dashboard proposal with data-source contracts and blast-radius controls
- Summary: Refined the compact-dashboard proposal, design, tasks, and wiki/wireframe artifacts with explicit source-contract policy (`pandas` as compute-only, `yfinance` bootstrap boundaries, provider graduation path), provenance/freshness requirements, module-level failure isolation, and feature-flag/kill-switch controls for high-risk research signals.
- Why: User requested senior-level blind-spot review and strict blast-radius control so the redesign is trustworthy under data gaps, staleness, and provider failures.
- Files: `openspec/changes/archive-v0-and-build-compact-trading-dashboard/{proposal.md,design.md,tasks.md,specs/frontend-compact-trading-dashboard/spec.md}`, `docs/product/{trading-dashboard-llm-wiki.md,two-tab-dashboard-wireframe-v1.md}`, `CHANGELOG.md`.
- Validation: Artifact-level consistency review plus external-source refresh for market-data policy and source strategy (`yfinance`, `pandas`, `SEC EDGAR`, provider docs), followed by OpenSpec strict validation for the updated change package.
- Notes: This remains planning-scope only; implementation work should start from the updated `tasks.md` sequence and preserve fail-fast unavailable states for unsupported contracts.

### docs(frontend-research,openspec): verify yfinance data surface and rebase proposal to yfinance-first extraction
- Summary: Performed an online documentation review of official yfinance API/docs/source and updated proposal/design/tasks/wiki/wireframe artifacts to prioritize yfinance-first extraction for v1, adding an explicit availability matrix (`direct`, `derived`, `unavailable`) for opportunity metrics and clarifying that provider migration is not a blocker for this phase.
- Why: User requested that planning prioritize available data now from yfinance (financial statements, ratios, options context, screening fields) before spending scope on provider strategy changes.
- Files: `openspec/changes/archive-v0-and-build-compact-trading-dashboard/{proposal.md,design.md,tasks.md}`, `docs/product/{trading-dashboard-llm-wiki.md,two-tab-dashboard-wireframe-v1.md}`, `CHANGELOG.md`.
- Validation: Online source review anchored on official yfinance documentation/reference pages plus repository source (`ticker.py`) and re-validation of OpenSpec change artifacts in strict mode.
- Notes: Proprietary signals (`J5`, `JR4`, green/red labels) and historical IV percentile remain non-native; proposal now enforces direct yfinance extraction and pandas derivation before any `unavailable` status.

### docs(frontend-research,openspec): integrate boneyard + awesome-design-md UX constraints and preserve compact quant-report gadget
- Summary: Refined compact-dashboard proposal/design/spec/tasks/wiki/wireframe artifacts with explicit storytelling contracts (`what/why/action/evidence`), phi-derived rhythm guidance (`1.613`), corner-token families (including large rounded emphasis controls), stable skeleton-loading requirements, and preservation requirements for a compact `My Portfolio` quant-report gadget with HTML export, analyst-pack export, scope selector, and date-range controls.
- Why: User requested senior-level UX/UI expectations grounded in provided reference repositories and asked to keep report-export functionality while improving compactness and readability.
- Files: `openspec/changes/archive-v0-and-build-compact-trading-dashboard/{proposal.md,design.md,tasks.md,specs/frontend-compact-trading-dashboard/spec.md,specs/frontend-dashboard-visual-system/spec.md}`, `docs/product/{trading-dashboard-llm-wiki.md,two-tab-dashboard-wireframe-v1.md}`, `CHANGELOG.md`.
- Validation: Reference review of `boneyard` docs/repo plus `awesome-design-md` repository and selected `DESIGN.md` examples, followed by OpenSpec strict re-validation.
- Notes: This remains planning-scope; full UI implementation should execute from updated tasks (`1.5`, `3.5`, `3.6`, `4.8`, `4.9`) before enabling advanced modules.

### docs(frontend-research,openspec): publish third-pass route and visualization refinement memo
- Summary: Added a new implementation-facing refinement memo that supersedes the earlier 2-tab wireframe for the next frontend pass, centers the dashboard on five routes (`home`, `analytics`, `risk`, `signals`, `asset-detail`), compresses quant depth into executive clarity, and formalizes chart grammar, information distribution, and compact utility placement for report/export actions.
- Why: The latest product direction requires a sharper executive/analytical separation and stricter visual grammar before any further frontend implementation proceeds.
- Files: `docs/product/portfolio-dashboard-third-pass-refinement.md`, `docs/product/{trading-dashboard-llm-wiki.md,two-tab-dashboard-wireframe-v1.md}`, `CHANGELOG.md`.
- Validation: Documentation cross-check against the existing OpenSpec change artifacts and the user-provided third-pass refinement context; no code/runtime changes required.
- Notes: The new memo is the preferred implementation steering document for the next agent pass; the earlier 2-tab wireframe is now explicitly marked superseded.

## 2026-04-12

### feat(frontend-dashboard,docs,openspec): execute phase-n dashboard professionalization and executive workspace system
- Summary: Implemented the full phase-n redesign slice by adding a route-aware dashboard visual system (lens/status tokens, typography roles, `hero|standard|utility` panel hierarchy), executive first-viewport route composition (`dominant-job`, `hero-insight`, support modules), support-rail shell framing, and governance extensions for promoted insights/chart-fit rules plus first-viewport templates; delivered route updates across Home, Holdings, Performance/Analytics, and Transactions with new fail-first contracts and test coverage.
- Why: Complete the OpenSpec professionalization pass so the dashboard behaves as an executive operator workspace with auditable governance and stronger first-surface clarity.
- Files: `frontend/src/{app/{styles.css,analytics-workspace.contract.test.ts,dashboard-information-architecture.contract.fail-first.test.ts,workspace-shell-navigation.contract.fail-first.test.ts,dashboard-visual-system.contract.fail-first.test.ts},components/{charts/WorkspaceChartPanel.tsx,workspace-layout/{PortfolioWorkspaceLayout.tsx,PortfolioWorkspaceLayout.test.tsx,PortfolioWorkspaceShell.test.tsx,WorkspacePrimaryJobPanel.tsx,WorkspaceStateBanner.tsx}},features/portfolio-workspace/{dashboard-governance.ts,state-copy.ts},pages/portfolio-{home,analytics,holdings,transactions}-page/*}`, `docs/{product/{portfolio-kpi-governance.md,phase-n-dashboard-implementation-handoff.md},guides/frontend-api-and-ux-guide.md}`, `openspec/changes/phase-n-dashboard-professionalization-and-executive-workspace-system/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test` (32 files / 157 tests passed), `rtk npm --prefix frontend run lint` (pass), `rtk npm --prefix frontend run build` (pass), `rtk openspec status --change phase-n-dashboard-professionalization-and-executive-workspace-system --json` (complete), `rtk openspec validate phase-n-dashboard-professionalization-and-executive-workspace-system --type change --strict --json` (pass).
- Notes: OpenSpec commands report non-blocking PostHog DNS flush warnings (`edge.openspec.dev`) in this sandboxed environment; build retains existing non-blocking Vite chunk-size warning.

## 2026-04-06

### feat(portfolio-decision-layer,portfolio-ml,portfolio-ai-copilot): implement phase-m backend contracts for command center, rebalancing/news context, clustering/anomalies, and structured copilot envelope
- Summary: Added decision-layer analytics endpoints (`/portfolio/command-center`, `/portfolio/exposure`, `/portfolio/contribution-to-risk`, `/portfolio/correlation`) with typed schemas and freshness metadata; introduced new read-only vertical slices for rebalancing strategy comparison (`/portfolio/rebalancing/strategies`) plus constrained scenario analysis (`/portfolio/rebalancing/scenario`) and holdings-grounded news context (`/portfolio/news/context`); extended portfolio ML with deterministic clustering/anomaly builders + endpoints (`/portfolio/ml/clusters`, `/portfolio/ml/anomalies`), quantile-boosting baseline policy support, percentile fields (`p10/p50/p90`) in forecast horizons, and governance lineage metadata (feature/policy versions + family stale reason semantics) in registry rows; migrated copilot response contracts to a structured envelope (`answer`, `evidence`, `assumptions`, `caveats`, `suggested_follow_ups`) with compatibility mapping and added guided phase-m question-pack resolver.
- Why: Phase-m fail-first contracts were red and the product lacked mounted decision-layer endpoints plus AI-native response structure needed for risk/rebalancing/copilot orchestration.
- Files: `app/{main.py,portfolio_analytics/{routes.py,schemas.py,service.py},portfolio_ml/{routes.py,schemas.py,service.py,tests/test_phase_m_forecast_policy_and_governance_extensions.py},portfolio_ai_copilot/{schemas.py,service.py},portfolio_rebalancing/{__init__.py,routes.py,schemas.py,service.py,tests/test_phase_m_rebalancing_and_news_readonly.py},portfolio_news_context/{__init__.py,routes.py,schemas.py,service.py}}`, `openspec/changes/phase-m-ai-native-portfolio-intelligence-productization/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk bash -lc "UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/main.py app/portfolio_analytics app/portfolio_ml app/portfolio_ai_copilot app/portfolio_rebalancing app/portfolio_news_context"` (pass), `rtk bash -lc "UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/main.py app/portfolio_analytics app/portfolio_ml app/portfolio_ai_copilot app/portfolio_rebalancing app/portfolio_news_context"` (pass), `rtk bash -lc "UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/main.py app/portfolio_analytics app/portfolio_ml app/portfolio_ai_copilot app/portfolio_rebalancing app/portfolio_news_context"` (0 errors), `rtk bash -lc "UV_CACHE_DIR=/tmp/uv-cache ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -q app/portfolio_rebalancing/tests/test_phase_m_rebalancing_and_news_readonly.py app/portfolio_ml/tests/test_phase_m_forecast_policy_and_governance_extensions.py app/portfolio_ml/tests/test_phase_m_segmentation_and_quantile_fail_first.py app/portfolio_ml/tests/test_forecast_policy_gates_fail_first.py app/portfolio_ml/tests/test_model_registry_contracts_fail_first.py app/portfolio_analytics/tests/test_phase_m_endpoint_contracts_fail_first.py app/portfolio_ai_copilot/tests/test_phase_m_structured_response_fail_first.py"` (20 passed).
- Notes: OpenSpec command output still shows non-blocking PostHog DNS flush warnings (`edge.openspec.dev`) after successful status output.

### test(frontend-phase-m): fix decision-lens page tests for new hooks and structured copilot UI
- Summary: Updated Home/Risk/Reports/Copilot page tests to mock newly introduced decision-layer hooks (`command-center`, `contribution-to-risk`, `anomalies`, `news-context`) and aligned assertions with structured copilot panel copy plus duplicated suggestion-chip rendering.
- Why: Full frontend test runs were failing after phase-m route and UI productization changes due missing query mocks and stale assertion text/routes.
- Files: `frontend/src/pages/portfolio-{home,risk,reports,copilot}-page/*.test.tsx`, `CHANGELOG.md`.
- Validation: `rtk npm run test -- src/pages/portfolio-home-page/PortfolioHomePage.test.tsx src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx` (51 passed), `rtk npm run lint` (pass), `rtk npm run test` (30 files / 144 tests passed), `rtk npm run build` (pass).
- Notes: Build keeps existing non-blocking Vite large-chunk warning.

### docs(product,openspec): align phase-m posture docs and capture implementation handoff notes
- Summary: Updated `README.md` and core product docs to reflect AI-native decision-layer posture (decision lenses, decision/ML/copilot capabilities, expanded API surface) and added phase-m implementation handoff notes with residual risks/follow-up items.
- Why: Phase-m task closeout required documentation and governance alignment with the shipped decision-layer frontend/backend contracts.
- Files: `README.md`, `docs/product/{prd.md,roadmap.md,portfolio-kpi-governance.md}`, `openspec/changes/phase-m-ai-native-portfolio-intelligence-productization/{tasks.md,implementation-handoff.md}`, `CHANGELOG.md`.
- Validation: `rtk openspec validate phase-m-ai-native-portfolio-intelligence-productization --type change --strict --json` (pass), `rtk openspec status --change 'phase-m-ai-native-portfolio-intelligence-productization' --json` (artifacts complete).
- Notes: OpenSpec PostHog DNS warnings (`edge.openspec.dev`) remain non-blocking in this environment.

## 2026-04-05

### feat(frontend-dashboard,docs): execute phase-l dashboard IA rationalization with audit registry and progressive disclosure
- Summary: Implemented phase-l dashboard IA contracts by adding deterministic route/widget governance metadata, fail-first IA contract tests (dominant primary job, module budgets, duplicate-question guardrails, progressive-disclosure requirements, shell-density policy), route-aware shell density modes (`expanded`/`balanced`/`compact`), and progressive-disclosure refactors on `Analytics`, `Risk`, and `Reports`; published full widget inventory + severity audit + disposition matrix + route wireframes.
- Why: Dashboard functionality had become visually and structurally overloaded, especially on Risk/Reports, reducing first-surface scanability and making route-level interpretation inconsistent.
- Files: `frontend/src/{features/portfolio-workspace/dashboard-governance.ts,components/workspace-layout/{PortfolioWorkspaceLayout.tsx,PortfolioWorkspaceLayout.test.tsx,WorkspacePrimaryJobPanel.tsx},components/charts/WorkspaceChartPanel.tsx,pages/portfolio-{home,analytics,risk,reports,transactions}-page/*.tsx,pages/portfolio-{analytics,risk,reports}-page/*.test.tsx,app/dashboard-information-architecture.contract.fail-first.test.ts,app/styles.css,features/portfolio-workspace/command-palette.ts}`, `docs/product/{phase-l-dashboard-audit-and-ia-rationalization.md,portfolio-kpi-governance.md}`, `docs/guides/{frontend-api-and-ux-guide.md,frontend-design-system-guide.md}`, `openspec/changes/phase-l-dashboard-audit-and-information-architecture-rationalization/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/app/dashboard-information-architecture.contract.fail-first.test.ts src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/pages/portfolio-transactions-page/PortfolioTransactionsPage.test.tsx` (pass), `rtk npm --prefix frontend run lint` (pass), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass), `rtk openspec status --change \"phase-l-dashboard-audit-and-information-architecture-rationalization\" --json` (artifacts complete), `rtk openspec validate phase-l-dashboard-audit-and-information-architecture-rationalization --type change --strict --json` (pass), `rtk openspec validate --specs --all` (pass).
- Notes: Holdings lens remains mapped to grouped summary and lot-detail routes (`/portfolio`, `/portfolio/:symbol`) while preserving current workspace route compatibility during first migration slice.

### feat(portfolio-ai-copilot,frontend-copilot): implement full DCA 2x opportunity-scan strategy with deterministic action states
- Summary: Reworked `opportunity_scan` from score-only ranking into a deterministic DCA strategy workflow that classifies each candidate as `double_down_candidate`, `baseline_dca`, `watchlist`, or `hold_off`; added 52-week drawdown metrics, DCA strategy request controls (`opportunity_strategy_profile`, `double_down_threshold_pct`, `double_down_multiplier`), fundamentals-proxy state/score/reason codes, and operation-specific narration prompts that explain deterministic DCA outputs with explicit proxy limitations.
- Why: Opportunity Scan lacked an actionable strategy policy, so users could not reliably operationalize DCA + double-down rules from the chat workspace.
- Files: `app/portfolio_ai_copilot/{schemas.py,service.py,tests/test_opportunity_scanner_fail_first.py}`, `frontend/src/{core/api/schemas.ts,features/portfolio-copilot/{api.ts,workspace-session.tsx},pages/portfolio-copilot-page/PortfolioCopilotPage.tsx,pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx}`, `docs/guides/{frontend-api-and-ux-guide.md,portfolio-ai-copilot-guide.md}`, `CHANGELOG.md`.
- Validation: `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run pytest -q app/portfolio_ai_copilot/tests/test_opportunity_scanner_fail_first.py` (pass), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run pytest -q app/portfolio_ai_copilot/tests -m 'not integration'` (22 passed, 2 deselected), `rtk npm --prefix frontend run test -- src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx` (8 passed), `rtk npm --prefix frontend run test -- src/components/workspace-layout/WorkspaceCopilotLauncher.fail-first.test.tsx` (7 passed), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run mypy app/portfolio_ai_copilot` (pass), `rtk env UV_CACHE_DIR=/tmp/.uv-cache uv run pyright app/portfolio_ai_copilot` (0 errors), `rtk npm --prefix frontend run build` (pass).
- Notes: Full `app/portfolio_ai_copilot/tests` run requires `ALLOW_INTEGRATION_DB_MUTATION=1` for integration-marked document-reference tests.

### feat(frontend-copilot,design): ship chat-first copilot presentation across header, docked pane, and expanded route
- Summary: Upgraded copilot UI to a chat-native presentation by adding chat header/nav variants in shared workspace shell, converting `WorkspaceCopilotComposer` into a timeline + composer + insight-panels layout, polishing docked/mobile launcher chrome, and refactoring `/portfolio/copilot` into a full chat-first route with deterministic opportunity/history as secondary modules; updated `DESIGNS.md` to v0.3 with an explicit copilot chat experience contract.
- Why: Current copilot functionality was strong but visually too control-panel oriented; this aligns UX with familiar chat interaction expectations while preserving read-only guardrails, evidence visibility, and deterministic candidate/narration separation.
- Files: `frontend/src/{components/app-shell/AppShell.tsx,components/workspace-layout/{PortfolioWorkspaceLayout.tsx,WorkspaceCopilotLauncher.tsx,WorkspaceCopilotLauncher.fail-first.test.tsx},pages/portfolio-copilot-page/PortfolioCopilotPage.tsx,app/styles.css}`, `DESIGNS.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/components/workspace-layout/WorkspaceCopilotLauncher.fail-first.test.tsx --run` (pass), `rtk npm --prefix frontend run test -- src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx --run` (pass), `rtk npm --prefix frontend run test -- src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx --run` (pass), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass), `rtk npm --prefix frontend run test` (132 passed).
- Notes: Build reports an existing Vite chunk-size warning for large bundles; no functional regression was detected.

### feat(frontend-copilot,ux): add business-grade financial recommendation bubbles and WhatsApp-style chat micro-polish
- Summary: Added curated, reusable financial recommendation bubbles in copilot composer with portfolio/business-oriented prompt language (allocation policy, benchmark-adjusted drivers, downside resilience, cashflow quality, concentration limits, rolling consistency, executive briefing), plus denser chat rhythm polish (avatar message rows, tighter bubble spacing, status-dot title, icon-first dock actions, tighter send bar ergonomics).
- Why: Users requested more familiar chat feel and stronger prompt quality for substantive portfolio intelligence conversations instead of simplistic risk-average checks.
- Files: `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.tsx`, `frontend/src/app/styles.css`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/components/workspace-layout/WorkspaceCopilotLauncher.fail-first.test.tsx --run` (pass), `rtk npm --prefix frontend run test -- src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx --run` (pass), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass).
- Notes: Existing build chunk-size warning remains unchanged and unrelated to this UX-focused update.

### feat(frontend-copilot,dca-ux): make recommendation bubbles operation-aware with DCA-focused prompt catalog
- Summary: Updated copilot recommendation bubbles to be operation-aware: `chat` keeps general portfolio strategy prompts, while `opportunity_scan` now surfaces DCA-specific, business-grade prompts focused on deployment policy, concentration controls, benchmark-relative resilience, and governance checks; backend prompt suggestions are now prioritized in the visible bubble set.
- Why: Improve practical guidance quality for users actively executing DCA workflows and keep quick-prompt language aligned with deterministic opportunity-scan decisions.
- Files: `frontend/src/components/workspace-layout/WorkspaceCopilotLauncher.tsx`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test -- src/components/workspace-layout/WorkspaceCopilotLauncher.fail-first.test.tsx --run` (pass), `rtk npm --prefix frontend run test -- src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx --run` (pass), `rtk npm --prefix frontend run type-check` (pass).
- Notes: No API contract changes were required; this is a presentation-layer prompt-catalog update.

### fix(portfolio-ai-copilot,dca-policy): block double-down classification when 52W history coverage is incomplete
- Summary: Hardened deterministic DCA action classification so `double_down_candidate` requires full 52-week history coverage (`>=252` points); candidates lacking full coverage now carry explicit reason codes (`insufficient_52w_history`, `double_down_threshold_not_evaluable`) and cannot trigger double-down state.
- Why: Prevent false-positive double-down recommendations caused by applying a 52W drawdown threshold to partial-history windows (for example 90–120 points), preserving policy integrity and audit clarity.
- Files: `app/portfolio_ai_copilot/service.py`, `app/portfolio_ai_copilot/tests/test_opportunity_scanner_fail_first.py`, `CHANGELOG.md`.
- Validation: `rtk env UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ai_copilot/tests/test_opportunity_scanner_fail_first.py::test_opportunity_scanner_does_not_double_down_without_full_52w_history` (pass), `rtk env UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ai_copilot/tests/test_opportunity_scanner_fail_first.py` (5 passed), `rtk env UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ai_copilot` (pass), `rtk npm --prefix frontend run test -- src/pages/portfolio-copilot-page/PortfolioCopilotPage.test.tsx --run` (pass), `rtk npm --prefix frontend run type-check` (pass).
- Notes: This fix keeps candidate eligibility broad while enforcing strict action-state gating for double-down policy.

### docs(design): add codebase-aligned `DESIGNS.md` baseline for workspace IA and contract-safe visualization rules
- Summary: Added a new repository-root `DESIGNS.md` (v0.2) that upgrades the earlier high-level proposal into an implementation-aligned design contract covering current route IA, active backend endpoint coverage, route-level UX jobs, chart/module selection tied to real payloads, unit/provenance guardrails, and explicit deferred scope boundaries.
- Why: The previous proposal was directionally strong but over-scoped relative to implemented routes/contracts; a codebase-aligned design document is needed so frontend/design/agent changes stay consistent with ledger-first fail-fast standards.
- Files: `DESIGNS.md`, `CHANGELOG.md`.
- Validation: Documentation cross-check against current route and contract sources: `rtk nl -ba frontend/src/app/router.tsx`, `rtk nl -ba app/portfolio_analytics/routes.py`, `rtk nl -ba app/portfolio_analytics/schemas.py`, `rtk nl -ba app/portfolio_ml/routes.py`, `rtk nl -ba app/portfolio_ai_copilot/routes.py`, `rtk nl -ba docs/standards/{frontend-standard.md,portfolio-visualization-standard.md}`.

### feat(portfolio-analytics,frontend-reports): add Markowitz efficient frontier API and reports visualization
- Summary: Added a new typed backend endpoint `GET /api/portfolio/efficient-frontier` with period/scope/symbol normalization, constrained `frontier_points`, deterministic long-only sampling, and explicit max-Sharpe/min-volatility outputs; integrated frontend API/hook/contracts and upgraded Quant Reports Advanced Risk Lab to render the efficient frontier curve, highlighted anchor points, methodology metadata, and max-Sharpe vs min-volatility weight table.
- Why: Efficient Frontier was previously not visible in the UI because there was no complete backend+frontend contract path for frontier data; this closes that gap and makes portfolio optimization context inspectable in-product.
- Files: `app/portfolio_analytics/{routes.py,schemas.py,service.py,tests/test_workspace_endpoint_contracts_fail_first.py}`, `frontend/src/{core/api/schemas.ts,features/portfolio-workspace/{api.ts,hooks.ts},pages/portfolio-reports-page/{PortfolioReportsPage.tsx,PortfolioReportsPage.test.tsx},app/styles.css}`, `CHANGELOG.md`.
- Validation: `rtk env ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py::test_efficient_frontier_endpoint_contract_exposes_frontier_points_and_weights app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py::test_efficient_frontier_endpoint_normalizes_scope_and_symbol_before_service_call` (2 passed), `rtk uv run mypy app/portfolio_analytics app/portfolio_ml app/main.py` (pass), `rtk uv run pyright app/portfolio_analytics app/portfolio_ml app/main.py` (0 errors), `rtk uv run ruff check app/portfolio_analytics/routes.py app/portfolio_analytics/service.py app/portfolio_analytics/schemas.py app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py` (pass), `rtk npm run type-check` (pass), `rtk npm run test -- src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx --run` (24 passed), `rtk npm run test -- --run` (132 passed), `rtk npm run build` (pass).

### docs(standards,docs): add portfolio visualization standard for passive-investor analytics UX
- Summary: Added `docs/standards/portfolio-visualization-standard.md` defining chart-selection taxonomy, route-level required visualization priorities, unit/contract guardrails, accessibility constraints, anti-pattern policy, and validation/test expectations aligned with existing portfolio workspace modules.
- Why: Portfolio chart quality and consistency needed one canonical standard to prevent trader-style drift, unit-format regressions (for example percent double-scaling), and inconsistent analytical framing across Home/Analytics/Risk/Reports surfaces.
- Files: `docs/standards/portfolio-visualization-standard.md`, `docs/README.md`, `docs/references/references.md`, `CHANGELOG.md`.
- Validation: Documentation review against current route/module contracts in `frontend/src/pages/portfolio-{home,analytics,risk,reports}-page/*` and API schemas in `frontend/src/core/api/schemas.ts` plus `app/portfolio_analytics/schemas.py`; external references refreshed from FT Visual Vocabulary, Tableau chart-selection docs, WCAG 2.2 understanding docs, and Portfolio Charts.

### feat(portfolio-ml,portfolio-ai-copilot): complete phase-i 6.x/7.x delivery with governed SQL, document references, and ML copilot grounding
- Summary: Completed OpenSpec change `phase-i-ml-timeseries-signal-and-forecasting` tasks `6.x` and `7.x` by adding copilot contract extensions (`document_ids`, `prompt_suggestions`), phase-i `portfolio_ml` allowlisted copilot tools (signals, CAPM, forecasts, registry), one governed SQL template path with allowlist/parameter/timeout controls, document-reference validation against persisted ingestion rows, and phase-i docs/runbook updates including one offline training/evaluation command script and guide.
- Why: Activate practical ML-to-copilot grounding and governed diagnostics while preserving strict read-only, fail-fast, and non-advice boundaries; close documentation and validation gates required for implementation handoff.
- Files: `app/portfolio_ai_copilot/{schemas.py,service.py,tests/test_ml_contract_extensions_fail_first.py,tests/test_governed_sql_template_policy_fail_first.py}`, `scripts/portfolio_ml/run_offline_training_eval.py`, `docs/{guides/portfolio-ml-phase-i-guide.md,guides/portfolio-ai-copilot-guide.md,product/roadmap.md,README.md}`, `openspec/changes/phase-i-ml-timeseries-signal-and-forecasting/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk uv run ruff check .` (pass), `rtk uv run black . --check --diff` (pass), `rtk uv run mypy app/` (pass), `rtk uv run pyright app/` (0 errors), `rtk uv run ty check app` (pass), `rtk env ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_ml/tests app/portfolio_ai_copilot/tests app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py` (73 passed), `rtk openspec validate --changes "phase-i-ml-timeseries-signal-and-forecasting" --strict` (pass), `rtk openspec validate --specs --all` (24/24 passed).
- Notes: OpenSpec PostHog flush DNS warnings (`edge.openspec.dev`) were non-fatal; validation results remained green.

### feat(frontend-workspace,portfolio-copilot): complete phase-j portfolio insight workspace and UX polish
- Summary: Completed OpenSpec change `phase-j-portfolio-insight-workspace-and-ux-polish` with a persistent workspace shell, route-owned first-viewport primary-job modules, command/context carryover primitives, persistent copilot launcher (desktop dock + mobile full-screen), cross-mode copilot continuity, and bounded prompt-suggestion plus `document_id` attachment references.
- Why: Stabilize analytical navigation and copilot continuity so users can move across Home/Analytics/Risk/Quant-Reports/Copilot without context loss, duplicated state messaging, or inconsistent first-view information architecture.
- Files: `frontend/src/{app/{router.tsx,providers.tsx,styles.css,analytics-workspace.contract.test.ts},components/workspace-layout/{PortfolioWorkspaceLayout.tsx,PortfolioWorkspaceLayout.test.tsx,PortfolioWorkspaceShell.test.tsx,WorkspaceCopilotLauncher.tsx,WorkspaceCopilotLauncher.fail-first.test.tsx,WorkspacePrimaryJobPanel.tsx,WorkspaceStateBanner.tsx},features/portfolio-workspace/{command-palette.ts,context-carryover.ts,core-ten-catalog.ts,state-copy.ts},features/portfolio-copilot/{api.ts,presentation.ts,workspace-session.tsx},pages/portfolio-{home,analytics,risk,reports,copilot}-page/*,core/api/schemas.ts}`, `docs/product/{portfolio-kpi-governance.md,phase-j-emil-design-polish-review.md}`, `openspec/changes/phase-j-portfolio-insight-workspace-and-ux-polish/tasks.md`, `CHANGELOG.md`.
- Validation: `rtk npm --prefix frontend run test` (127 passed), `rtk npm --prefix frontend run lint` (pass), `rtk npm --prefix frontend run type-check` (pass), `rtk npm --prefix frontend run build` (pass), `rtk uv run pytest -v app/portfolio_ai_copilot/tests` (20 passed, 2 integration-env errors), `rtk env ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_ai_copilot/tests/test_ml_contract_extensions_fail_first.py` (3 passed), `rtk openspec validate --changes "phase-j-portfolio-insight-workspace-and-ux-polish" --strict` (pass).
- Notes: OpenSpec telemetry DNS warnings (`edge.openspec.dev`) remained non-fatal; change status is `all_done` (25/25 tasks complete) and ready to archive.

## 2026-04-04

### feat(portfolio-ai-copilot,frontend-workspace): deliver phase-h read-only AI layering slice with Groq adapter, deterministic opportunity scan, and copilot workspace
- Summary: Implemented OpenSpec change `phase-h-ai-layering-read-only-portfolio-copilot` through backend `portfolio_ai_copilot` slice delivery (typed contracts, safety boundary enforcement, allowlisted tool orchestration, Groq OpenAI-compatible adapter, deterministic opportunity scoring, stable provider/runtime reason mapping) and frontend `/portfolio/copilot` workspace delivery (explicit `idle/loading/blocked/error/ready` states, evidence + limitation surfaces, separated opportunity candidates vs AI narration, and navigation integration).
- Why: Activate a narrow, production-usable AI layer over existing deterministic portfolio analytics while preserving fail-fast boundaries, privacy minimization, and non-advice posture.
- Files: `app/portfolio_ai_copilot/{schemas.py,service.py,routes.py,provider_groq.py,tests/*}`, `app/{core/config.py,main.py}`, `frontend/src/{app/router.tsx,app/styles.css,core/api/schemas.ts,components/workspace-layout/PortfolioWorkspaceLayout.tsx,components/workspace-layout/PortfolioWorkspaceLayout.test.tsx,features/portfolio-copilot/{api.ts,hooks.ts},pages/portfolio-copilot-page/*}`, `docs/{guides/portfolio-ai-copilot-guide.md,guides/frontend-api-and-ux-guide.md,guides/validation-baseline.md,product/{roadmap.md,backlog-sprints.md},README.md}`, `.env.example`, `openspec/changes/phase-h-ai-layering-read-only-portfolio-copilot/tasks.md`, `CHANGELOG.md`.
- Validation: `uv run ruff check app/` (pass), `uv run black app --check --diff` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ty check app` (pass), `uv run pytest -v app/portfolio_ai_copilot/tests` (15 passed), `env ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_ai_copilot/tests app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py` (43 passed), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run test` (112 passed), `npm --prefix frontend run build` (pass), `openspec validate phase-h-ai-layering-read-only-portfolio-copilot --type change --strict --json` (pass), `openspec validate --specs --all --json` (22/22 passed).
- Notes: Provider configuration is intentionally fail-fast (no fallback provider chain) and now documented with explicit Groq project key/spend-limit/model-permission guidance.

## 2026-03-31

### fix(dev-workflow): make justfile parseable and correct db-check URL normalization
- Summary: Fixed `justfile` recipe parsing by indenting embedded Python heredoc blocks under `db-upgrade` and `test-db-upgrade`, replaced `db-check` with a direct SQLAlchemy `SELECT 1` connectivity probe, and added `db-upgrade` drift recovery to stamp `head` when upgrade fails before running existing missing-table self-heal.
- Why: `just dev-local` was blocked before execution with `Unknown start of token '.'` due unindented heredoc bodies being treated as top-level `justfile` syntax.
- Files: `justfile`, `CHANGELOG.md`.
- Validation: `rtk just --list` (pass), `rtk just db-check` (pass), `rtk just dev-local` (passes guard/connectivity, recovers migration drift via stamp-to-head path, starts backend on `http://127.0.0.1:8123`).
- Notes: This change is intentionally minimal and does not alter runtime behavior beyond fixing recipe parsing.

## 2026-03-30

### feat(frontend-workspace,ux-polish): harden dense-table readability and compact control surfaces for phase-g 9.x
- Summary: Implemented extension `9.x` for `phase-g-quantstats-monte-carlo-and-risk-evolution` by shipping hierarchy default sector-collapsed state with explicit sortable-header arrows, semantic Quant lens table rendering, compact Quant report lifecycle control grouping, and contribution-table semantic label hardening (`signed contribution`, `net share`, `absolute share`) without changing contribution math.
- Why: Workspace modules were functionally correct but still had readability and professionalism gaps in dense analytical tables and oversized control surfaces.
- Files: `frontend/src/{features/portfolio-hierarchy/PortfolioHierarchyTable.tsx,pages/portfolio-reports-page/PortfolioReportsPage.tsx,pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx,app/styles.css}`, `frontend/src/{features/portfolio-hierarchy/PortfolioHierarchyTable.test.tsx,pages/portfolio-reports-page/PortfolioReportsPage.test.tsx,pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx}`, `openspec/changes/phase-g-quantstats-monte-carlo-and-risk-evolution/{tasks.md,design.md,specs/frontend-analytics-workspace/spec.md}`, `docs/{guides/frontend-api-and-ux-guide.md,product/{roadmap.md,backlog-sprints.md,frontend-ux-analytics-expansion-roadmap.md}}`, `CHANGELOG.md`.
- Validation: `npm --prefix frontend test -- --run src/features/portfolio-hierarchy/PortfolioHierarchyTable.test.tsx src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx` (31 passed), `npm --prefix frontend run lint` (pass), `npm --prefix frontend test` (101 passed), `npm --prefix frontend run build` (pass), `openspec validate --changes "phase-g-quantstats-monte-carlo-and-risk-evolution" --strict` (pass).
- Notes: OpenSpec emitted telemetry/PostHog network flush warnings (`edge.openspec.dev` DNS) after successful validation; change validation result remained green.

### feat(portfolio-health,frontend-workspace): add deterministic health synthesis scoring and KPI-priority context across Home/Risk/Reports
- Summary: Implemented the `phase-g` health-synthesis extension by adding backend `portfolio/health-synthesis` contracts (score, label, profile posture, pillar metrics, key drivers, caveats), extending quant report payloads with optional health summary, and wiring new Home/Risk/Quant-Reports modules that prioritize the Core 10 KPI layer with posture-aware interpretation context.
- Why: KPI volume in QuantStats output was making portfolio-health interpretation hard for non-expert users; this adds an explicit, deterministic analyst-style synthesis without replacing the raw metric detail.
- Files: `app/portfolio_analytics/{schemas.py,service.py,routes.py,tests/test_health_synthesis_policy_fail_first.py,tests/test_workspace_endpoint_contracts_fail_first.py}`, `frontend/src/{core/api/schemas.ts,features/portfolio-workspace/{api.ts,hooks.ts},pages/portfolio-{home,risk,reports}-page/*}`, `openspec/changes/phase-g-quantstats-monte-carlo-and-risk-evolution/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `ALLOW_INTEGRATION_DB_MUTATION=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_health_synthesis_policy_fail_first.py app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py -k "health_synthesis"` (4 passed), `cd frontend && npm test -- --run src/pages/portfolio-home-page/PortfolioHomePage.test.tsx src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx` (38 passed), `cd frontend && npm run build` (pass), `openspec validate --changes "phase-g-quantstats-monte-carlo-and-risk-evolution" --strict` (pass).
- Notes: `openspec` emitted PostHog flush warnings (`edge.openspec.dev` DNS) in this environment after successful validation; change/spec results remained valid.

### feat(portfolio-analytics,portfolio-reports): add profile-calibrated Monte Carlo comparison and portfolio P&L semantic hardening
- Summary: Extended Monte Carlo contracts and UI with default-on three-profile comparison (`Conservative`, `Balanced`, `Growth`), calibration-basis controls (`monthly`, `annual`, `manual`), explicit calibration metadata/fallback semantics, and one-run deterministic profile probability outputs; upgraded Quant/Reports controls with profile toggle/basis/apply actions and panoramic comparison matrix; refined Home/Analytics copy to keep portfolio P&L semantics explicit (realized/unrealized/period P&L context).
- Why: Users needed immediate side-by-side scenario interpretation instead of single-threshold inspection, plus clearer KPI semantics that match portfolio investing workflows.
- Files: `app/portfolio_analytics/{schemas.py,service.py,routes.py,tests/test_quantstats_adapter_fail_first.py,tests/test_workspace_endpoint_contracts_fail_first.py}`, `frontend/src/{core/api/schemas.ts,pages/portfolio-reports-page/{PortfolioReportsPage.tsx,PortfolioReportsPage.test.tsx},features/portfolio-workspace/overview.ts,pages/portfolio-home-page/PortfolioHomePage.tsx,pages/portfolio-analytics-page/PortfolioAnalyticsPage.tsx,app/styles.css}`, `docs/{guides/frontend-api-and-ux-guide.md,standards/quantstats-standard.md,product/{roadmap.md,backlog-sprints.md}}`, `openspec/changes/phase-g-quantstats-monte-carlo-and-risk-evolution/tasks.md`, `CHANGELOG.md`.
- Validation: `ALLOW_INTEGRATION_DB_MUTATION=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py -k "monte_carlo or profile"` (10 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics` (pass), `uv run pyright app/portfolio_analytics` (0 errors), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run test -- src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/pages/portfolio-home-page/PortfolioHomePage.test.tsx src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.test.tsx` (30 passed), `npm --prefix frontend run build` (pass), `openspec validate phase-g-quantstats-monte-carlo-and-risk-evolution --type change --strict --json` (pass).
- Notes: OpenSpec/PostHog telemetry flush warnings were network-related (`edge.openspec.dev` unreachable) and did not affect change validation results.

### fix(portfolio-reports,portfolio-analytics): harden Monte Carlo horizon constraints and upgrade simulation form UX
- Summary: Fixed Monte Carlo horizon contract mismatch for short periods by lowering API/schema minimum horizon to 5 days, introducing realistic period defaults (`30D->20`, `90D->60`, `252D->126`), clamping backend default horizons to available return history, and returning actionable insufficiency errors with available-day context; upgraded Quant/Reports Monte Carlo form with structured field cards, period-aware horizon guidance, suggested-horizon reset action, and warning-level lifecycle copy for insufficient-history cases.
- Why: Users were hitting confusing Monte Carlo failures (for example `30D` period with 30-day horizon) due off-by-one return-count realities and non-actionable error presentation; form controls also needed more professional information architecture.
- Files: `app/portfolio_analytics/{schemas.py,service.py,tests/test_quantstats_adapter_fail_first.py}`, `frontend/src/{core/api/schemas.ts,pages/portfolio-reports-page/{PortfolioReportsPage.tsx,PortfolioReportsPage.test.tsx},app/styles.css}`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py` (5 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics` (pass), `uv run pyright app/portfolio_analytics` (0 errors), `npm --prefix frontend run test -- src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx` (22 passed), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run build` (pass).
- Notes: Monte Carlo terminal-percentile collapse behavior from QuantStats shuffled-return simulations remains explicitly surfaced in UI; distribution-model evolution can be handled as a separate backend enhancement.

### docs(product,openspec): add phase-h AI layering proposal and post-MVP copilot roadmap slice
- Summary: Added `Phase 10 / Sprint 9` planning entries for a post-MVP read-only portfolio copilot, replaced generic AI deferral language with a narrow approved first slice plus explicit non-goals, and created OpenSpec change `phase-h-ai-layering-read-only-portfolio-copilot` with implementation-ready proposal, design, specs, and tasks artifacts.
- Why: The core ledger, market-data, analytics, and workspace foundations are now strong enough to support a scoped AI layer, but the repository needed explicit guardrails to prevent drift into raw-data chat, execution workflows, or broad template adoption.
- Files: `docs/product/{roadmap.md,backlog-sprints.md}`, `openspec/changes/phase-h-ai-layering-read-only-portfolio-copilot/{proposal.md,design.md,tasks.md,specs/portfolio-ai-copilot/spec.md,specs/frontend-ai-copilot-workspace/spec.md}`, `CHANGELOG.md`.
- Validation: `openspec status --change "phase-h-ai-layering-read-only-portfolio-copilot" --json` (`isComplete: true`), `openspec instructions apply --change "phase-h-ai-layering-read-only-portfolio-copilot" --json` (`state: ready`, 24 tasks pending), `openspec validate phase-h-ai-layering-read-only-portfolio-copilot --type change --strict --json` (pass), `openspec validate --specs --all --json` (21/21 passed).
- Notes: This entry documents planning and governance work only; no backend or frontend AI runtime was implemented in this change set.

### feat(portfolio-analytics,frontend): implement phase-g quantstats monte carlo and risk-evolution contracts
- Summary: Implemented OpenSpec change `phase-g-quantstats-monte-carlo-and-risk-evolution` by adding typed backend contracts and services for risk evolution (`/risk-evolution`), return distribution (`/return-distribution`), and bounded Monte Carlo (`/monte-carlo`), extending risk estimator metadata (units, interpretation bands, timeline linkage), and upgrading Risk + Quant/Reports UI with timeline/distribution modules and explicit Monte Carlo lifecycle states.
- Why: Snapshot-only risk and quant diagnostics were insufficient for long-term investing interpretation; users needed deterministic trajectory and scenario context with explicit assumptions and fail-fast boundaries.
- Files: `app/portfolio_analytics/{routes.py,schemas.py,service.py,tests/test_workspace_endpoint_contracts_fail_first.py,tests/test_quantstats_adapter_fail_first.py}`, `frontend/src/{core/api/schemas.ts,features/portfolio-workspace/{api.ts,hooks.ts},components/charts/PortfolioRiskEvolutionCharts.tsx,pages/portfolio-{risk,reports}-page/*,app/styles.css,components/charts/{PortfolioCharts.test.tsx,WorkspaceChartComposition.fail-first.test.tsx}}`, `docs/{guides/frontend-api-and-ux-guide.md,standards/quantstats-standard.md,product/{roadmap.md,backlog-sprints.md,frontend-ux-analytics-expansion-roadmap.md}}`, `openspec/changes/phase-g-quantstats-monte-carlo-and-risk-evolution/tasks.md`, `CHANGELOG.md`.
- Validation: `ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -q app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py` (28 passed), `uv run ruff check .` (pass), `uv run black app --check --diff` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ty check app` (pass), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run test` (88 passed), `npm --prefix frontend run build` (pass), `openspec validate phase-g-quantstats-monte-carlo-and-risk-evolution --type change --strict --json` (pass), `openspec validate --specs --all --json` (pass).
- Notes: Local `black . --check` output was polluted by generated `.uv-cache` vendor files; project-source check was executed on `app/` to match repository Python source gate scope.

### docs(product-roadmap): add mandatory refactor and code-health checkpoint phase/sprint
- Summary: Added a new mandatory refactor checkpoint to product planning by introducing `Phase 8: Refactor and Code Health Checkpoint (Mandatory)` in the roadmap and `Sprint 7: Refactor and Code Health Checkpoint (Mandatory)` in the backlog with explicit quality, contract, docs, and evidence closeout gates.
- Why: Delivery has been feature-heavy; a dedicated checkpoint is required to systematically reduce technical debt, recover contract consistency, and prevent quality drift before opening new feature work.
- Files: `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `CHANGELOG.md`.
- Validation: Documentation update reviewed for phase/sprint sequencing, gate clarity, and consistency with existing roadmap/backlog structure.
- Notes: This checkpoint is intentionally non-feature by default and must be completed before the next major feature phase.

### docs(openspec): sync delta specs for phase-f-dashboard-and-quant-ux-hardening change
- Summary: Merged delta specifications from change 'phase-f-dashboard-and-quant-ux-hardening' into main specs, adding requirements for route-agnostic quant API contracts, dedicated Quant/Reports surface, shared chart composition, KPI explainability, and release readiness validations.
- Why: Delta specs needed to be integrated into the canonical specification repository to maintain up-to-date documentation for AI agents and developers.
- Files: `openspec/specs/{frontend-analytics-workspace,frontend-kpi-governance,frontend-release-readiness,portfolio-analytics}/spec.md`, `CHANGELOG.md`.
- Validation: Verified delta spec content matches main spec additions, no conflicts or overwrites of existing requirements.
- Notes: New spec created for frontend-kpi-governance; others updated with additions and modifications.

### docs(frontend,quantstats): align phase-f API and metric docs with shipped behavior
- Summary: Updated frontend UX/API and QuantStats standards documentation to reflect shipped Phase-F contracts, including time-series `scope`/`instrument_symbol` query behavior and the expanded risk estimator set (`volatility_annualized`, `max_drawdown`, `beta`, `downside_deviation_annualized`, `value_at_risk_95`, `expected_shortfall_95`).
- Why: Documentation needed to match the implemented backend/frontend behavior and remove ambiguity for future implementation and QA work.
- Files: `docs/guides/frontend-api-and-ux-guide.md`, `docs/standards/quantstats-standard.md`, `CHANGELOG.md`.
- Validation: `rg -n "scope|instrument_symbol|downside_deviation_annualized|value_at_risk_95|expected_shortfall_95" docs/guides/frontend-api-and-ux-guide.md docs/standards/quantstats-standard.md` (pass, expected contracts present).
- Notes: Documentation-only update; no application code or test contract behavior changed.

## 2026-03-29

### feat(frontend-workspace,portfolio-analytics): ship analyst UX hardening for reports/risk plus scoped heatmap contracts
- Summary: Implemented Phase-F hardening for Reports and Risk by adding instrument-scoped time-series contracts (`scope` + `instrument_symbol`) on `/portfolio/time-series`, redesigning risk visualization into unit-aware range tracks plus a compact metric ledger with explainability popovers, adding heatmap scope/symbol controls, and upgrading contribution analysis with top-mover summaries and magnitude bars; also removed the obsolete `Ledger-only v1` badge, converted theme toggle to icon-only UI, and improved trust-pill provenance truncation/readability.
- Why: Resolve non-professional UX friction seen in test walkthroughs (unclear contribution table, weak risk visual meaning, noisy metadata chips, obsolete labels) while preserving deterministic API contracts and fail-fast behavior.
- Files: `app/portfolio_analytics/{routes.py,schemas.py,service.py,tests/test_routes.py,tests/test_workspace_endpoint_contracts_fail_first.py}`, `frontend/src/{app/styles.css,app/router.tsx,components/{app-shell/AppShell.tsx,app-shell/AppShell.test.tsx,theme-toggle/ThemeToggle.tsx,workspace-layout/PortfolioWorkspaceLayout.tsx,workspace-layout/PortfolioWorkspaceLayout.test.tsx,charts/PortfolioRiskChart.tsx,charts/AnalystVisualModules.tsx,charts/WorkspaceChartPanel.tsx},core/api/schemas.ts,features/portfolio-workspace/{api.ts,hooks.ts,overview.ts},pages/portfolio-{home,risk,reports}-page/*,app/analytics-workspace.contract.test.ts}`, `docs/{guides/frontend-api-and-ux-guide.md,product/frontend-ux-analytics-expansion-roadmap.md,standards/quantstats-standard.md}`, `openspec/changes/phase-f-dashboard-and-quant-ux-hardening/{design.md,specs/*,tasks.md}`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics` (pass), `uv run pyright app/portfolio_analytics` (0 errors), `cd frontend && npm run test -- src/pages/portfolio-reports-page/PortfolioReportsPage.test.tsx src/pages/portfolio-risk-page/PortfolioRiskPage.test.tsx src/components/app-shell/AppShell.test.tsx` (17 passed), `cd frontend && npm run test -- src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx src/pages/portfolio-home-page/PortfolioHomePage.test.tsx src/app/analytics-workspace.contract.test.ts` (19 passed), `cd frontend && npm run lint` (pass), `cd frontend && npm run build` (pass).
- Notes: Two backend integration-route tests for seeded DB state (`test_time_series_endpoint_supports_instrument_scope_with_symbol_filter`, `test_quant_report_generation_normalizes_timezone_before_quantstats_html`) are blocked in this sandbox due local Postgres socket permission denial (`PermissionError: [Errno 1] Operation not permitted` on `::1:5432`), not due assertion regressions.

### feat(portfolio-analytics,frontend): align QuantStats phase-2 resilience, reporting contracts, and Home UX boundaries
- Summary: Completed OpenSpec change `align-quantstats-phase2-home-resilience-and-reporting` by finalizing QuantStats adapter compatibility behavior, optional benchmark omission metadata, bounded quant report generation/retrieval contracts, Home section-scoped quant/report resilience, explicit preview-vs-interpretation route labeling, and deterministic hierarchy control accessibility updates.
- Why: Quant/report capabilities needed to be added without regressing Home reliability, while keeping fail-fast explicitness and deterministic frontend behavior.
- Files: `app/portfolio_analytics/{service.py,routes.py,schemas.py,tests/test_quantstats_adapter_fail_first.py,tests/test_quant_report_artifact_lifecycle.py,tests/test_time_series_benchmark_overlays.py,tests/test_routes.py,tests/test_workspace_endpoint_contracts_fail_first.py}`, `frontend/src/{pages/portfolio-home-page/*,pages/portfolio-analytics-page/*,pages/portfolio-risk-page/*,components/workspace-layout/*,features/portfolio-hierarchy/*,features/portfolio-workspace/*,core/api/{client.ts,schemas.ts},app/styles.css}`, `docs/standards/quantstats-standard.md`, `docs/{README.md,guides/frontend-api-and-ux-guide.md,product/frontend-ux-analytics-expansion-roadmap.md}`, `openspec/changes/align-quantstats-phase2-home-resilience-and-reporting/{proposal.md,design.md,specs/*,tasks.md}`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics app/core/config.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_analytics app/core/config.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_quant_dependency_policy.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_quant_report_artifact_lifecycle.py app/portfolio_analytics/tests/test_time_series_benchmark_overlays.py` (7 passed), `ALLOW_INTEGRATION_DB_MUTATION=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests/test_quant_dependency_policy.py app/portfolio_analytics/tests/test_quantstats_adapter_fail_first.py app/portfolio_analytics/tests/test_quant_report_artifact_lifecycle.py app/portfolio_analytics/tests/test_time_series_benchmark_overlays.py app/portfolio_analytics/tests/test_routes.py -k "quant_report_generation or quant_report_artifact_retrieval or quant_report_retrieval or quant_metrics"` (5 passed, 19 deselected), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run test` (69 passed), `npm --prefix frontend run build` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app frontend` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app frontend/scripts --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` (pass), `OPENSPEC_TELEMETRY=0 openspec validate align-quantstats-phase2-home-resilience-and-reporting --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (17/17 passed).
- Notes: A separate full `app/portfolio_analytics/tests` integration run showed pre-existing route-suite state-coupling failures outside this QuantStats/report target slice; targeted quant/report suites for this change are green.

### docs(frontend-roadmap): add Phase F for analyst-led KPI design and dashboard/quant UX hardening
- Summary: Extended the frontend analytics roadmap with a new Phase F that formalizes data-analyst KPI ownership, dashboard IA refinement, chart duplication/spacing cleanup, and Quant report UX relocation from Home into a dedicated analytical context.
- Why: Current workspace delivery still carries chart duplication and spacing inconsistencies, and users need a more professional analytical dashboard model with clearer Quant report workflow placement.
- Files: `docs/product/frontend-ux-analytics-expansion-roadmap.md`, `CHANGELOG.md`.
- Validation: `ALLOW_INTEGRATION_DB_MUTATION=1 UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_routes.py -k "quant_report_generation_returns_retrievable_html_artifact or quant_report_artifact_retrieval_rejects_unavailable_report_id"` (2 passed), `npm --prefix frontend run test -- src/pages/portfolio-home-page/PortfolioHomePage.test.tsx -t "quant report"` (2 passed, 8 skipped), `git diff --check` (pass).
- Notes: Validation confirms base report generation/retrieval path in tests; runtime report UX issues are now explicitly tracked in Phase F scope.

### feat(frontend-analytics-workspace): implement Phase F 4.x chart governance, Quant/Reports IA, and explainability surfaces
- Summary: Implemented Phase F frontend IA and visualization hardening by shipping a dedicated `Quant/Reports` route/test surface, moving Home to snapshot-only behavior, standardizing chart composition with shared workspace chart panels across Home/Analytics/Risk, adding analyst modules (period-change waterfall, contribution waterfall, monthly returns heatmap), adding KPI/metric explainability popovers (Home KPIs, trend tooltip metric, risk estimator cards, quant scorecards), and removing tooltip false-affordance controls.
- Why: The workspace needed senior-analyst storytelling structure, deterministic route ownership, and professional explainability/action integrity instead of route-coupled report flows and ambiguous tooltip actions.
- Files: `frontend/src/{app/analytics-workspace.contract.test.ts,app/router.tsx,app/styles.css,components/charts/{AnalystVisualModules.tsx,PortfolioCharts.test.tsx,PortfolioTrendChart.tsx,WorkspaceChartPanel.tsx},components/metric-explainability/MetricExplainabilityPopover.tsx,components/workspace-layout/{PortfolioWorkspaceLayout.tsx,PortfolioWorkspaceLayout.test.tsx},core/api/schemas.ts,pages/portfolio-{home,analytics,risk,reports}-page/*}`, `docs/{product/frontend-ux-analytics-expansion-roadmap.md,guides/frontend-api-and-ux-guide.md,standards/quantstats-standard.md}`, `openspec/changes/phase-f-dashboard-and-quant-ux-hardening/{specs/frontend-analytics-workspace/spec.md,specs/frontend-release-readiness/spec.md,tasks.md}`, `CHANGELOG.md`.
- Validation: `npm --prefix frontend test` (23 files, 80 tests passed), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run build` (pass; bundle-size warning only), `uv run mypy app/portfolio_analytics` (pass), `uv run pyright app/portfolio_analytics` (0 errors), `uv run ruff check app/portfolio_analytics` (pass), `ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_analytics/tests/test_routes.py -k "quant_report_generation_returns_retrievable_html_artifact or quant_report_generation_rejects_invalid_scope_parameters_explicitly or quant_report_generation_rejects_extra_request_context_fields or quant_report_artifact_retrieval_rejects_unavailable_report_id or quant_report_generation_keeps_read_only_side_effect_boundaries"` (5 passed), `ALLOW_INTEGRATION_DB_MUTATION=1 uv run pytest -v app/portfolio_analytics/tests/test_workspace_endpoint_contracts_fail_first.py -k "quant_report_generation_rejects_home_route_context_fields_explicitly or quant_report_generation_exposes_explicit_lifecycle_metadata"` (2 passed), `OPENSPEC_TELEMETRY=0 openspec validate phase-f-dashboard-and-quant-ux-hardening --type change --strict` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --strict` (18/18 passed).
- Notes: OpenSpec telemetry is disabled in this environment (`OPENSPEC_TELEMETRY=0`) to avoid non-blocking DNS telemetry flush noise.

## 2026-03-28

### feat(frontend-workspace): close OpenSpec 5.x with navigation coverage, workspace evidence, and docs sync
- Summary: Completed `expand-frontend-ux-and-analytics-workspace` task group `5.x` by adding workspace keyboard/navigation test coverage, extending frontend evidence harnesses to include workspace routes and analytics/risk API fixtures, capturing fresh accessibility/keyboard/CWV artifacts for `2026-03-28`, and syncing frontend guide/standard/roadmap/checklist documentation to implemented workspace contracts and deferred boundaries.
- Why: Change closeout required implementation-grade quality evidence and documentation parity before marking the proposal implementation-ready.
- Files: `frontend/src/components/workspace-layout/PortfolioWorkspaceLayout.test.tsx`, `frontend/scripts/{capture-frontend-evidence.mjs,measure-cwv.mjs}`, `docs/evidence/frontend/{accessibility-scan-2026-03-28.*,keyboard-walkthrough-2026-03-28.*,cwv-report-2026-03-28T04-35-40.732Z.json,cwv-report-2026-03-28.md,screenshots-2026-03-28/*}`, `docs/guides/{frontend-api-and-ux-guide.md,frontend-delivery-checklist.md}`, `docs/standards/frontend-standard.md`, `docs/product/frontend-ux-analytics-expansion-roadmap.md`, `openspec/changes/expand-frontend-ux-and-analytics-workspace/tasks.md`, `CHANGELOG.md`.
- Validation: `npm --prefix frontend run build` (pass), `npm --prefix frontend run frontend:evidence` (pass), `npm --prefix frontend run cwv:measure` (pass), `npm --prefix frontend run lint` (pass), `npm --prefix frontend run test` (62 passed), `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed).
- Notes: Evidence scripts were executed with elevated permissions in this environment due local-socket sandbox restrictions.

### fix(test-typing): make quant dependency policy tests pyright-strict compatible
- Summary: Refactored `app/portfolio_analytics/tests/test_quant_dependency_policy.py` to coerce TOML objects through explicit typed helpers and remove `Unknown`-typed access paths in strict pyright.
- Why: 5.4 validation gates require `pyright app/` to pass; strict unknown-type failures were blocking closeout.
- Files: `app/portfolio_analytics/tests/test_quant_dependency_policy.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_quant_dependency_policy.py` (pass).

### docs/workflow: harden ci-equivalent env handling and network-aware security gate behavior
- Summary: Updated local environment templates to quote `APP_NAME` values, switched `just` lint gate to `black --check --diff --workers 1` for constrained-runtime compatibility, added `scripts/security/run-pip-audit.sh` wrapper to classify DNS/network outages as blocked evidence when explicitly enabled, and documented the CI scripting rule to avoid `source .env`.
- Why: Recent CI-equivalent runs showed avoidable shell/env parsing drift and sandbox/network constraints; these changes preserve strict defaults while adding explicit, controlled behavior for restricted environments.
- Files: `.env`, `.env.example`, `justfile`, `scripts/security/run-pip-audit.sh`, `docs/guides/validation-baseline.md`, `CHANGELOG.md`.
- Validation: `git diff --check` (pass), `PIP_AUDIT_ALLOW_NETWORK_BLOCKED=1 bash scripts/security/run-pip-audit.sh` (classified network-blocked as intended in restricted environment).
- Notes: Security gate remains strict by default; blocked-network classification requires explicit opt-in via `PIP_AUDIT_ALLOW_NETWORK_BLOCKED=1`.

### docs(openspec): resolve implementation blockers in frontend analytics workspace change
- Summary: Resolved previously open planning blockers in `expand-frontend-ux-and-analytics-workspace` by freezing v1 chart library decision (`Recharts`), freezing Transactions route scope to ledger events only, and freezing chart-period enum contracts (`30D`, `90D`, `252D`, `MAX`) with explicit rejection semantics; propagated these decisions into proposal/design/spec/tasks artifacts.
- Why: Planning review identified unresolved design decisions as blocking safe `/execute`; closing them removes contract ambiguity and reduces rework risk during implementation.
- Files: `openspec/changes/expand-frontend-ux-and-analytics-workspace/{proposal.md,design.md,tasks.md,specs/portfolio-analytics/spec.md,specs/portfolio-risk-estimators/spec.md,specs/frontend-analytics-workspace/spec.md}`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (pass), `git diff --check` (pass).
- Notes: `design.md` Open Questions is now explicitly `None.` for this change.

### docs(openspec): harden frontend analytics workspace change with NumPy/pandas/SciPy operations contract
- Summary: Updated `expand-frontend-ux-and-analytics-workspace` artifacts (`proposal`, `design`, `tasks`, and related specs) to incorporate implementation-ready quant guidance from new NumPy/pandas/SciPy standards, including operations-first preprocessing invariants, frozen default risk windows (`30/90/252`), required estimator methodology metadata, approved baseline method families, and explicit SciPy non-convergence failure behavior.
- Why: The previous change had stack-selection coverage but still lacked concrete computational contract detail needed to execute risk-estimator implementation deterministically and consistently.
- Files: `openspec/changes/expand-frontend-ux-and-analytics-workspace/{proposal.md,design.md,tasks.md,specs/portfolio-risk-estimators/spec.md,specs/portfolio-analytics/spec.md,specs/frontend-analytics-workspace/spec.md,specs/frontend-release-readiness/spec.md}`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed).
- Notes: Review was performed against current repository diffs and the newly added standards docs for NumPy/pandas/SciPy.

### docs(standards): deepen pandas standard with operations-first finance patterns
- Summary: Expanded `docs/standards/pandas-standard.md` with an operations-first workflow for finance time-series, approved calculation method matrix, canonical metric recipes (returns, cumulative performance, volatility, drawdown, beta, OHLC), finance-specific pitfalls/guards, and stronger test guidance for deterministic metric regression.
- Why: The prior version was too general; portfolio analytics work needs explicit pandas method guidance for financial calculations and safer operational semantics.
- Files: `docs/standards/pandas-standard.md`, `CHANGELOG.md`.
- Validation: `git diff --check` (pass).
- Notes: Guidance and links were based on official pandas documentation only.

### docs(standards): add official NumPy, pandas, and SciPy standards
- Summary: Added three new standards documents (`numpy-standard`, `pandas-standard`, `scipy-standard`) aligned to existing repository standards format, including scope, installation policy, fail-fast rules, typing/performance guidance, and validation commands; updated docs navigation and references index accordingly.
- Why: The project needs explicit, reusable standards for the approved quant stack so implementation remains consistent, auditable, and aligned with repository engineering gates.
- Files: `docs/standards/{numpy-standard.md,pandas-standard.md,scipy-standard.md}`, `docs/README.md`, `docs/references/references.md`, `CHANGELOG.md`.
- Validation: Documentation update reviewed against official docs for NumPy, pandas, and SciPy; `git diff --check` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (pass).
- Notes: Sources were restricted to official documentation endpoints for all three libraries.

### docs(openspec): archive `add-market-enriched-portfolio-kpis` and sync portfolio-analytics spec
- Summary: Archived the completed OpenSpec change `add-market-enriched-portfolio-kpis` into `openspec/changes/archive/2026-03-28-add-market-enriched-portfolio-kpis` and applied its delta updates to the main `portfolio-analytics` spec.
- Why: Finalize the delivered market-enriched KPI slice and keep canonical specs aligned with implemented behavior before continuing new changes.
- Files: `openspec/specs/portfolio-analytics/spec.md`, `openspec/changes/archive/2026-03-28-add-market-enriched-portfolio-kpis/**`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec archive add-market-enriched-portfolio-kpis -y` (pass; reported `portfolio-analytics: update`, totals `+3, ~1`), `OPENSPEC_TELEMETRY=0 openspec list --json` (change no longer listed as active).
- Notes: Archive was executed with spec sync enabled (no `--skip-specs`), preserving the change history under `openspec/changes/archive/`.

### docs(openspec): formalize quant stack decision with accepted/rejected package policy
- Summary: Extended change `expand-frontend-ux-and-analytics-workspace` with an explicit quant dependency decision, adding approved package scope (`numpy`, `pandas`, `scipy`), optional overlay boundary (`pandas-ta`), rejected package list for v1, and new implementation tasks/spec requirements for pinning and dependency-guard coverage.
- Why: The prior proposal described analytics capabilities but did not formally lock the quantitative library stack, leaving reproducibility and implementation governance under-specified.
- Files: `openspec/changes/expand-frontend-ux-and-analytics-workspace/{proposal.md,design.md,tasks.md,specs/portfolio-risk-estimators/spec.md}`, `docs/product/frontend-ux-analytics-expansion-roadmap.md`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (17/17 passed).
- Notes: This is a decision-and-governance update; dependency installation/pinning in `pyproject.toml` + `uv.lock` remains tracked as execution tasks in the change.

### docs(openspec): create apply-ready change for frontend analytics workspace expansion
- Summary: Created OpenSpec change `expand-frontend-ux-and-analytics-workspace` with complete artifacts (`proposal.md`, `design.md`, `specs/*`, `tasks.md`) to operationalize the frontend UX/analytics expansion and risk-estimator rollout.
- Why: Move from high-level planning into an implementation-ready contract with explicit requirements, technical decisions, and trackable tasks aligned to repository standards.
- Files: `openspec/changes/expand-frontend-ux-and-analytics-workspace/{proposal.md,design.md,tasks.md,specs/frontend-analytics-workspace/spec.md,specs/portfolio-risk-estimators/spec.md,specs/portfolio-analytics/spec.md,specs/frontend-release-readiness/spec.md}`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec status --change "expand-frontend-ux-and-analytics-workspace" --json` (`isComplete=true`), `OPENSPEC_TELEMETRY=0 openspec validate expand-frontend-ux-and-analytics-workspace --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (17/17 passed).
- Notes: The change keeps `React + Vite` as immediate implementation baseline and defers any full Next.js migration to a later gated spike.

### docs(frontend): add ultimate-react-course SOT analysis and frontend UX/analytics expansion roadmap
- Summary: Added a formal frontend reference-SOT analysis for `jonasschmedtmann/ultimate-react-course` (architecture patterns, adoption matrix, governance boundaries, risks) and a new phased roadmap to prioritize UX/UI and analytics expansion before any optional Next.js migration decision.
- Why: Product direction now requires stronger frontend usability and analytics depth, plus persistent repository context for team-aligned standards, patterns, and migration criteria.
- Files: `docs/references/ultimate-react-course-frontend-sot-analysis.md`, `docs/product/frontend-ux-analytics-expansion-roadmap.md`, `docs/README.md`, `CHANGELOG.md`.
- Validation: In-depth repository inspection completed from local clone at commit `5c38ad0e9f5067d4a486e8ee5d7bed36268fbbb8` including architecture/dependency walkthrough of `16-fast-react-pizza`, `17-the-wild-oasis`, `21-the-wild-oasis-website`, and `22-nextjs-pages-router`; documentation-only update (no runtime code changes).
- Notes: Governance is explicit: this repository remains implementation authority; the course repository is adopted as frontend pattern reference SOT, not copy-paste implementation baseline.

## 2026-03-27

### feat(portfolio-analytics): deliver market-enriched summary KPIs with snapshot provenance across API, frontend, and docs
- Summary: Implemented one-snapshot market-enriched portfolio summary behavior end-to-end by adding internal snapshot-coverage resolution, bounded valuation fields/provenance in backend + frontend contracts, explicit summary `409` coverage rejection, updated summary UI rendering/copy for pricing provenance, and aligned product/guides docs with the new phase-6 analytics boundary.
- Why: Phase 6 KPI completion required moving summary analytics from ledger-only output to trusted persisted market-data enrichment without expanding into lot-detail valuation, FX-sensitive inference, public market-data routes, or ledger mutation.
- Files: `app/market_data/service.py`, `app/portfolio_analytics/{schemas.py,service.py,tests/test_routes.py}`, `frontend/src/{core/api/schemas.ts,features/portfolio-summary/*,pages/portfolio-summary-page/*,app/styles.css}`, `docs/product/{roadmap.md,decisions.md,frontend-mvp-prd-addendum.md}`, `docs/guides/{portfolio-ledger-and-analytics-guide.md,frontend-api-and-ux-guide.md,validation-baseline.md}`, `openspec/changes/add-market-enriched-portfolio-kpis/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_market_enriched_contract.py app/portfolio_analytics/tests/test_grouped_summary_formulas.py app/portfolio_analytics/tests/test_snapshot_consistency.py` (8 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_analytics/tests/test_routes.py -k "summary_endpoint_returns_grouped_rows_with_as_of_ledger_at or summary_endpoint_rejects_missing_open_position_price_coverage" -m integration` (2 passed, 2 deselected), `cd frontend && npm run lint` (pass), `cd frontend && npm run test` (26 passed), `cd frontend && npm run test -- src/core/api/schemas.market-enriched.test.ts src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx` (7 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/service.py app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/tests/test_routes.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/market_data/service.py app/portfolio_analytics/schemas.py app/portfolio_analytics/service.py app/portfolio_analytics/tests/test_routes.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed).
- Notes: Summary valuation fields stay bounded to persisted USD-compatible snapshot coverage; closed-position rows keep valuation fields nullable by contract; lot-detail remains ledger-only.

### fix(deps): upgrade cryptography to address pip-audit blocker CVE
- Summary: Updated locked dependency `cryptography` from `46.0.5` to `46.0.6`.
- Why: `just ci` security gate (`pip-audit`) was blocked by `CVE-2026-34073` affecting `cryptography 46.0.5`.
- Files: `uv.lock`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv lock --upgrade-package cryptography` (pass, `46.0.5 -> 46.0.6`), full `just ci` equivalent rerun (pass: backend checks, DB-backed tests, frontend checks, pre-push hooks).

### fix(test-db-bootstrap): make local integration setup deterministic for non-admin app roles
- Summary: Hardened `test-db-upgrade` to bootstrap missing test DBs with explicit owner/schema privilege repair, added optional `TEST_DATABASE_ADMIN_URL` support for admin-only bootstrap flows, and documented the sequence in local workflow guides.
- Why: Local DB integration runs were repeatedly failing with sequence-sensitive setup issues (`database does not exist`, `permission denied for schema public`) that pushed operators into brute-force reruns instead of deterministic preflight.
- Files: `justfile`, `.env.example`, `docs/guides/{local-workflow-justfile.md,validation-baseline.md}`, `CHANGELOG.md`.
- Validation: Full local CI-equivalent gate executed successfully after bootstrap fix (`ruff`, `black --check`, `mypy`, `pyright`, `ty`, `bandit`, `pip-audit --ignore-vuln CVE-2026-4539`, `alembic upgrade` on `TEST_DATABASE_URL`, `pytest -m "not integration"` => 181 passed, `pytest -m "integration and not market_scope_heavy"` => 39 passed, frontend lint/type/test/build, pre-push hooks).

### test(market-data-verification): reduce full scope-100 soak cost while preserving rerun signal with smaller sample
- Summary: Converted the optional `market_scope_heavy` scope-100 integration lane from two full runs to one full run, and added a separate reduced-sample scope-100 rerun integration test to preserve insert/update idempotency coverage with lower runtime cost.
- Why: The previous full-100 double-run consumed more local CPU/time than needed for routine confidence, while the rerun behavior can be validated on a smaller deterministic subset.
- Files: `app/market_data/tests/test_service_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/tests/test_service_integration.py` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_scope_100_executes_once_and_non_mutating app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_scope_100_sample_rerun_is_idempotent_and_non_mutating -m integration --durations=5` (2 passed; call durations ~0.98s and ~0.44s), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest --collect-only -q app/market_data/tests/test_service_integration.py -m "integration and not market_scope_heavy"` (10/11 collected, 1 deselected).

### fix(ci-market-refresh): remove stale scope-200 heavy selector from workflow dispatch
- Summary: Updated CI workflow-dispatch heavy market-scope options to remove `200`, aligned default integration marker selection to `integration and not market_scope_heavy`, and simplified manual heavy execution so `all` resolves to the existing `market_scope_heavy` lane.
- Why: The repository no longer defines `market_scope_very_heavy` tests, so keeping a `200` CI path produced deterministic false failures (`no tests ran`, exit code 5) during manual dispatch.
- Files: `.github/workflows/ci.yml`, `CHANGELOG.md`.
- Validation: `rg -n "market_scope_very_heavy|heavy_market_scope|200" .github/workflows/ci.yml` (only `heavy_market_scope` and `100` remain), `git diff --check` (pass).

### fix(test-db): harden local integration migration order and prevent shared-test schema drift
- Summary: Added drift self-heal logic to `test-db-upgrade` so test DB setup repairs the known `alembic_version=head` + missing-table state before integration runs, and narrowed shared-test fixture teardown to `test_*` tables only to prevent dropping application schema tables from the active local database.
- Why: Repeated local integration failures were caused by sequence-sensitive schema drift, where full integration could pass once and then fail on subsequent runs because required tables were dropped while migration revision metadata remained at head.
- Files: `justfile`, `app/shared/tests/conftest.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/shared/tests/conftest.py` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/shared/tests/test_models.py -m integration` (3 passed), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q -m "integration and not market_scope_heavy"` (38 passed, 182 deselected), post-run schema check confirmed `alembic_version=7d5f2f8f9c3b` with `missing_tables=[]`.

### test(market-data-operations): rebalance local refresh verification to core-required plus representative non-core smoke
- Summary: Removed the routine scope-200 integration lane, clarified full scope-100 coverage as optional manual soak, and tightened the default integration contract around `core` plus representative non-core PR smoke; aligned `pytest` markers, `just` integration selectors, and market-data integration test labeling with that posture.
- Why: Full-scope 100/200 verification was creating disproportionate runtime/CPU pressure for local workflows, slowing routine validation without improving near-term readiness for the current portfolio-backed scope.
- Files: `app/market_data/tests/test_service_integration.py`, `pyproject.toml`, `justfile`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `.codex/commands/self-heal-ci.md`, `openspec/changes/rebalance-market-refresh-verification-scope/**`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/tests/test_service_integration.py app/data_sync/tests/test_data_sync_operations_cli.py` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/data_sync/tests/test_data_sync_operations_cli.py` (7 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest --collect-only -q app/market_data/tests/test_service_integration.py -m "integration and not market_scope_heavy"` (9/10 collected, 1 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest --collect-only -q app/market_data/tests/test_service_integration.py -m "integration and market_scope_heavy"` (1/10 collected, 9 deselected), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run alembic stamp base && PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (pass), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m "integration and not market_scope_heavy"` (38 passed, 182 deselected), `OPENSPEC_TELEMETRY=0 openspec validate rebalance-market-refresh-verification-scope --type change --strict --json` (pass), `OPENSPEC_TELEMETRY=0 openspec validate --specs --all --json` (16/16 passed), `git diff --check` (pass).
- Notes: Runtime refresh selector support (`core|100|200`) remains unchanged by design; this change rebalances verification posture only.

### chore(dependabot): reduce dependency PR noise with grouped weekly policy
- Summary: Reworked `.github/dependabot.yml` to use explicit weekly windows in `America/Santiago`, capped open PR volume per ecosystem (`uv=4`, `npm=3`, `github-actions=2`), grouped non-major updates (`minor`/`patch`) into single PR streams per ecosystem, and added dedicated grouped security-update tracks.
- Why: The repository had too many concurrent one-package Dependabot PRs, which increased review overhead and made dependency maintenance less predictable.
- Files: `.github/dependabot.yml`, `CHANGELOG.md`.
- Validation: configuration diff reviewed for ecosystem coverage (`uv`, `npm`, `github-actions`), grouped update semantics, and PR limit controls; `git diff --check` (pass).
- Notes: Major-version updates remain separate PRs by design for manual review.

### docs(commands): harden self-heal-ci defaults and approval guardrails
- Summary: Tightened `/self-heal-ci` to conservative defaults (`target=fast`, `using=back`, `max=2`, `autofix=off`), limited default autofix to non-semantic lint/format repairs, added protected-path stop conditions, and required explicit `confirm=high-risk` opt-in before broad/high-impact fixes.
- Why: CI healing command behavior was too broad for a controlled verification workflow and could unintentionally alter security/infrastructure/database-adjacent areas without explicit human approval.
- Files: `.codex/commands/self-heal-ci.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: documentation policy review against current `just` gate semantics; fallback integration marker scope aligned to `not market_scope_heavy and not market_scope_very_heavy`; `git diff --check` (pass).
- Notes: this change intentionally shifts `/self-heal-ci` from auto-repair-first to diagnose-first unless high-risk mode is explicitly approved.

### fix(ci-secrets): align local pre-push and CI gitleaks configuration for PR-range scans
- Summary: Added shared gitleaks config (`.gitleaks.toml`), introduced a reusable PR-range scan script (`scripts/security/run-gitleaks-pr-range.sh`), added `just secret-scan-pr`, rewired pre-push secret scanning to call the same PR-range workflow, pinned CI gitleaks action configuration/version to reduce local-vs-GH drift, and added a narrow allowlist for one historical false-positive token that cannot be removed without force-push history rewrite.
- Why: Local staged secret checks were passing while GitHub PR secret scans still failed on commit-history findings; the repository needed a simpler non-Docker workflow that scans PR-equivalent history locally before push.
- Files: `.gitleaks.toml`, `scripts/security/run-gitleaks-pr-range.sh`, `.pre-commit-config.yaml`, `justfile`, `.github/workflows/ci.yml`, `docs/guides/local-workflow-justfile.md`, `CHANGELOG.md`.
- Validation: `bash scripts/security/run-gitleaks-pr-range.sh origin/main` (pass after allowlist), `uvx --from pre-commit python -m pre_commit run --all-files --hook-stage pre-push` (pass), `git diff --check` (pass).
- Notes: Requires local `gitleaks` binary availability (`brew install gitleaks`). The allowlist is intentionally narrow (`docs/evidence/market-data/staged-live-smoke-2026-03-26.md` + exact historical token regex) to avoid broad suppression.

## 2026-03-26

### docs(market-data-operations): capture core/100 live smoke evidence and defer 200 from current closeout scope
- Summary: Recorded fresh market-data smoke evidence for standalone `core` and `100` plus one combined `data-sync-local --refresh-scope core` run in a dedicated artifact; updated OpenSpec change artifacts and operator/product docs so this closeout cycle validates `core -> 100`, treats blocked outcomes as first-class evidence, and marks `200` smoke as explicit deferred follow-up scope.
- Why: Current live runs showed meaningful operational blockers and runtime pressure; the repository needed an honest readiness posture based on executable evidence rather than waiting on long `200` cycles in this proposal.
- Files: `docs/evidence/market-data/staged-live-smoke-2026-03-26.md`, `docs/evidence/market-data/staged-live-smoke-template.md`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md,local-workflow-justfile.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `openspec/changes/capture-staged-market-refresh-live-smoke-evidence/{proposal.md,design.md,tasks.md,specs/market-data-operations/spec.md}`, `CHANGELOG.md`.
- Validation: live smoke commands executed (`market-refresh-yfinance --refresh-scope core` blocked with `502` TSLA currency metadata access failure, bounded `market-refresh-yfinance --refresh-scope 100` blocked with timeout payload `408`, `data-sync-local --refresh-scope core` completed with typed payload); `openspec validate capture-staged-market-refresh-live-smoke-evidence --type change --strict --json` (pass); `openspec validate --specs --all --json` (16/16 passed); `git diff --check` (pass).
- Notes: Additional ad hoc reruns were terminated when they became redundant/noisy; canonical evidence for this slice is the dated artifact above.

### feat(market-data-refresh): stabilize yfinance live-provider coverage with bounded fallback diagnostics
- Summary: Added configurable yfinance semantic recovery controls (`market_data_yfinance_history_fallback_periods`, `market_data_yfinance_default_currency`) and implemented bounded empty-history fallback (`5y -> 3y -> 1y -> 6mo` default) plus explicit default-currency assignment for missing metadata while preserving fail-fast behavior for unsupported payloads and explicit invalid currency values; extended refresh result/schema and scope metadata to expose `history_fallback_symbols`, `history_fallback_periods_by_symbol`, and `currency_assumed_symbols`; propagated typed evidence through data-sync surfaces and CLI tests.
- Why: Phase-6 operational refresh was blocked by predictable live-provider gaps (`empty history`, missing currency metadata). The repo needed explicit, auditable recovery without broad graceful degradation or relaxed required-symbol failure semantics.
- Files: `app/core/{config.py,tests/test_config.py}`, `app/market_data/{providers/yfinance_adapter.py,schemas.py,service.py,tests/test_yfinance_adapter_unit.py,tests/test_service_unit.py}`, `app/data_sync/{schemas.py,service.py,tests/test_data_sync_operations_cli.py}`, `README.md`, `docs/guides/{yfinance-integration-guide.md,validation-baseline.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `openspec/changes/stabilize-yfinance-live-provider-coverage/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/core/tests/test_config.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py app/data_sync/tests/test_data_sync_operations_cli.py` (53 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/market_data/tests/test_yfinance_adapter_unit.py::test_fetch_raises_explicit_error_when_history_fallback_ladder_is_exhausted app/market_data/tests/test_service_unit.py::test_refresh_core_surfaces_exhausted_history_fallback_for_required_symbols` (2 passed; explicit blocker-path evidence), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check ...` (pass on touched scope), `UV_CACHE_DIR=/tmp/uv-cache uv run black --check ...` (pass on touched scope), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass), `openspec validate stabilize-yfinance-live-provider-coverage --type change --strict --json` (pass), `openspec validate --specs --all --json` (16/16 passed).
- Notes: OpenSpec emitted non-blocking PostHog DNS flush warnings (`edge.openspec.dev`) in the restricted network sandbox after successful validation output.

## 2026-03-25

### fix(dev-workflow): isolate runtime and test databases in just recipes
- Summary: Added `db-runtime-guard` to `just dev` to block running the app against a test database or a shared dev/test URL, and introduced `test-db-check` + `test-db-upgrade` so `just test` and `just test-integration` require and use `TEST_DATABASE_URL` instead of mutating runtime `DATABASE_URL`.
- Why: Local development sessions were repeatedly showing empty data after test runs because integration/unit test paths truncate or recreate tables and were targeting the same database as runtime.
- Files: `justfile`, `.env.example`, `README.md`, `CHANGELOG.md`.
- Validation: `justfile` recipe logic reviewed end-to-end for URL resolution from env/`.env`, runtime-vs-test separation checks, and DATABASE_URL override behavior on pytest/alembic test paths.
- Notes: Existing local `.env` files must define `TEST_DATABASE_URL` to use updated test recipes.

### fix(market-data-refresh): set single-retry default and add per-symbol request pacing
- Summary: Updated yfinance defaults to one retry (`market_data_yfinance_max_retries=1`) and introduced configurable per-symbol pacing (`market_data_yfinance_request_spacing_seconds`, default `1.0`); wired pacing through refresh-plan adapter config and staged per-symbol refresh loops while preserving strict `core` and bounded `100/200` tolerance behavior.
- Why: Reduce throttling exposure in live runs and keep retry behavior conservative/predictable while maintaining fail-fast coverage guarantees for required portfolio symbols.
- Files: `app/core/config.py`, `app/market_data/{providers/yfinance_adapter.py,service.py,tests/test_yfinance_adapter_unit.py,tests/test_service_unit.py}`, `app/core/tests/test_config.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/core/tests/test_config.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` (40 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/core/config.py app/core/tests/test_config.py app/market_data/providers/yfinance_adapter.py app/market_data/service.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/core/config.py app/market_data/providers/yfinance_adapter.py app/market_data/service.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_yfinance_adapter_unit.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/core/config.py app/market_data/providers/yfinance_adapter.py app/market_data/service.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black --check --diff app/core/config.py app/core/tests/test_config.py app/market_data/providers/yfinance_adapter.py app/market_data/service.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` (pass).

### feat(market-data-refresh): allow partial-success retries for starter scopes while keeping core strict
- Summary: Updated `refresh_yfinance_supported_universe` so `core` remains strict fail-fast, while `100/200` scopes fetch per symbol, run one retry pass for first-pass failures, persist successful rows, and report retry/failure diagnostics (`retry_attempted_symbols*`, `failed_symbols*`) in the typed refresh result.
- Why: Live provider behavior is intermittently unstable; operators need controlled onboarding at `100/200` without blocking the entire refresh when only non-portfolio symbols fail, while still failing immediately if required portfolio coverage cannot be recovered.
- Files: `app/market_data/{service.py,schemas.py,tests/test_service_unit.py,tests/test_service_integration.py}`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/market_data/tests/test_service_unit.py` (18 passed), `PYTHONPATH=. UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/data_sync/tests/test_data_sync_operations_cli.py` (7 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/market_data/service.py app/market_data/schemas.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_service_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/market_data/service.py app/market_data/schemas.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/market_data/service.py app/market_data/schemas.py` (0 errors), `BLACK_NUM_WORKERS=1 UV_CACHE_DIR=/tmp/uv-cache uv run black app/market_data/service.py app/market_data/schemas.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_service_integration.py --check --diff` (pass), integration target `app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_scope_100_is_idempotent_and_non_mutating -m integration` blocked in sandbox (`PermissionError: [Errno 1] Operation not permitted` opening PostgreSQL socket).

### feat(market-data-operations): add staged refresh-scope propagation and operator onboarding smoke evidence
- Summary: Added explicit refresh-scope propagation (`core` default, `100`, `200`) across market-data refresh, data-sync orchestration, CLI, and `just` command surfaces; extended typed refresh evidence to carry `refresh_scope_mode` and `requested_symbols_count`; added/updated unit/integration/CLI tests for scope validation, defaulting, propagation, and idempotency; and documented staged onboarding/validation workflow updates across guides and product planning artifacts.
- Why: Operators need controlled real-data onboarding (`core -> 100 -> 200`) with explicit scope-aware evidence and fail-fast diagnostics before widening live refresh scope.
- Files: `app/market_data/{schemas.py,service.py,tests/test_service_unit.py,tests/test_service_integration.py}`, `app/data_sync/service.py`, `scripts/data_sync_operations.py`, `app/data_sync/tests/test_data_sync_operations_cli.py`, `justfile`, `docs/guides/{yfinance-integration-guide.md,local-workflow-justfile.md,validation-baseline.md}`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `openspec/changes/add-incremental-market-refresh-modes-core-100-200/tasks.md`, `CHANGELOG.md`.
- Validation: `PYTHONPATH=. uv run pytest -q app/data_sync/tests/test_data_sync_operations_cli.py` (7 passed), `uv run pytest -q app/market_data/tests/test_service_unit.py` (16 passed), `uv run pytest -q app/market_data/tests/test_service_integration.py` (9 passed), `uv run pytest -v -m integration` (38 passed), `uv run ruff check app/market_data/service.py app/market_data/schemas.py app/market_data/tests/test_service_integration.py app/data_sync/service.py scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` (pass), `uv run mypy app/` (pass), `uv run pyright app/market_data/service.py app/market_data/schemas.py app/data_sync/service.py scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` (0 errors), `uv run alembic stamp base && uv run alembic upgrade head` (drift repair pass), staged live smoke: `core` blocked (`502`, empty history for `QQQM`), `100` blocked (`502`, missing currency metadata for `AMD`), `200` blocked (`502`, missing currency metadata for `XLF`).
- Notes: Running the full integration marker suite currently leaves schema drift when shared test fixtures drop all tables; operator commands should run behind `db-upgrade` self-heal (or explicit `stamp base + upgrade head`) before manual smoke runs.

### feat(market-data-universe): add versioned yfinance starter libraries with portfolio-minimum guarantees
- Summary: Replaced hardcoded market-data symbol scope with a validated JSON universe contract (`required_portfolio_symbols`, `core_refresh_symbols`, `starter_100_symbols`, `starter_200_symbols`), added service accessors for starter-library retrieval, introduced a generator script and `just` recipe to rebuild the universe, and checked in the first generated `v1` universe file.
- Why: Operations needed an explicit, versioned symbol library for expansion planning while guaranteeing that current portfolio symbols remain included at minimum and keeping the active refresh scope deterministic.
- Files: `app/market_data/service.py`, `app/market_data/symbol_universe.v1.json`, `scripts/build_market_symbol_universe.py`, `justfile`, `docs/guides/{yfinance-integration-guide.md,local-workflow-justfile.md}`, `app/core/{config.py,tests/test_config.py}`, `app/market_data/tests/test_service_unit.py`, `CHANGELOG.md`.
- Validation: `uv run python -m scripts.build_market_symbol_universe` (generated universe), `python3` contract check (`required=19`, `starter_100=100`, `starter_200=200`, subset checks pass), `uv run pytest -q app/core/tests/test_config.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_yfinance_adapter_unit.py` (34 passed), `uv run ruff check app/market_data/service.py app/market_data/providers/yfinance_adapter.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_yfinance_adapter_unit.py app/core/config.py app/core/tests/test_config.py scripts/build_market_symbol_universe.py` (pass), `uv run black --check ...` (pass), `uv run mypy app/market_data/service.py app/market_data/providers/yfinance_adapter.py app/core/config.py` (pass), `uv run pyright app/market_data/service.py app/market_data/providers/yfinance_adapter.py app/core/config.py` (0 errors), `uv run ty check app/market_data/service.py app/market_data/providers/yfinance_adapter.py app/core/config.py` (pass).
- Notes: `core_refresh_symbols` remains portfolio-minimum scope for fail-fast operational refresh; starter 100/200 libraries are available for controlled onboarding and expansion.

### fix(yfinance-adapter): harden currency metadata access when fast_info/info properties raise
- Summary: Added safe mapping-attribute access in `_fetch_symbol_currency` so provider property-access exceptions (for example `KeyError('currency')`) no longer escape as unexpected failures, while preserving explicit 502 fail-fast behavior when currency metadata is truly unavailable.
- Why: Manual smoke evidence showed environment-dependent `KeyError: 'currency'` failures that blocked operational refresh despite existing fallback intent.
- Files: `app/market_data/providers/yfinance_adapter.py`, `app/market_data/tests/test_yfinance_adapter_unit.py`, `CHANGELOG.md`.
- Validation: `uv run pytest -q app/market_data/tests/test_yfinance_adapter_unit.py::test_fetch_currency_falls_back_to_info_when_fast_info_property_access_raises_key_error app/market_data/tests/test_yfinance_adapter_unit.py::test_fetch_currency_raises_adapter_error_when_info_property_access_raises_key_error` (pass), `uv run pytest -q app/market_data/tests/test_service_unit.py app/market_data/tests/test_yfinance_adapter_unit.py` (29 passed).

### chore(openspec): disable local telemetry to suppress non-blocking DNS flush noise
- Summary: Added `OPENSPEC_TELEMETRY=0` to local environment defaults and documented the export step in validation guidance so OpenSpec runs stay clean in restricted-network environments.
- Why: OpenSpec PostHog DNS flush warnings (`edge.openspec.dev`) were non-blocking but noisy during normal validation and archive workflows.
- Files: `.env`, `.env.example`, `docs/guides/validation-baseline.md`, `CHANGELOG.md`.
- Validation: `OPENSPEC_TELEMETRY=0 openspec validate stabilize-market-data-operations-runbook-and-scheduling-posture --type change --strict --json` (pass; warning no longer emitted).

### fix(market-data-operations): stabilize yfinance temporal-key handling and formalize operator blocker evidence
- Summary: Hardened `yfinance` trading-date coercion for approved live day-level temporal variants (`date`/`datetime`, `to_pydatetime()` to `date`/`datetime`, scalar `item()` conversions), improved unexpected provider-error detail in fail-fast 502 paths, added deterministic unit/integration coverage for the stabilized adapter path, and updated product/operator/provider docs to freeze runbook evidence rules and schedule-ready invocation posture.
- Why: Phase 6 required the operational refresh workflow to be implementation-ready without weakening fail-fast behavior; live smoke outcomes needed to remain auditable as explicit blocker evidence when provider/runtime conditions prevent safe completion.
- Files: `app/market_data/providers/yfinance_adapter.py`, `app/market_data/tests/{test_yfinance_adapter_unit.py,test_service_integration.py}`, `scripts/data_sync_operations.py`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md,local-workflow-justfile.md}`, `docs/standards/yfance-standard.md`, `openspec/changes/stabilize-market-data-operations-runbook-and-scheduling-posture/tasks.md`, `CHANGELOG.md`.
- Validation: `uv run pytest -v app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py app/data_sync/tests/test_data_sync_operations_cli.py` (28 passed), `uv run pytest -v -m integration app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_adapter_item_keys_are_idempotent_and_non_mutating app/market_data/tests/test_service_integration.py::test_supported_universe_refresh_is_idempotent_and_non_mutating` (2 passed), `uv run ruff check app/market_data/providers/yfinance_adapter.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_integration.py scripts/data_sync_operations.py` (pass), `uv run black ... --check --diff` (pass), `uv run mypy app/market_data/providers/yfinance_adapter.py scripts/data_sync_operations.py` (pass), `uv run pyright app/market_data/providers/yfinance_adapter.py scripts/data_sync_operations.py` (0 errors), `uv run ty check app/market_data/providers/yfinance_adapter.py` (pass), `uv run python -m scripts.data_sync_operations data-sync-local --snapshot-captured-at 2026-03-25T00:00:00Z` (initial run blocked at `market_refresh` with 502 `KeyError: 'currency'`; post-fix rerun completed with `status=completed`, `requested_symbols_count=19`, `inserted_prices=23505`), `openspec validate stabilize-market-data-operations-runbook-and-scheduling-posture --type change --strict --json` (pass), `openspec validate --specs --all --json` (15/15 passed).
- Notes: OpenSpec commands emitted PostHog DNS flush warnings (`edge.openspec.dev`) after command completion; validation outcomes remained successful.

### docs(commands): tighten proposal-to-plan handoff and add change-ready orchestrator
- Summary: Updated `/next-proposal` to emit explicit branch/propose/plan handoff commands, updated `/new-branch` examples and next-action guidance for proposal-first workflows, extended `/plan` with a standardized implementation handoff block, and added a new `/change-ready` command that guides proposal discovery through plan-ready state while stopping before `/execute`.
- Why: The repository workflow needed a cleaner human-in-the-loop path from "what should we do next?" to "this change is ready for implementation," especially when proposal/planning and implementation are split across different models.
- Files: `.codex/commands/{next-proposal.md,new-branch.md,plan.md,change-ready.md,README.md}`, `CHANGELOG.md`.
- Validation: Documentation-only change; command contracts reviewed for consistency with branch-first proposal creation, OpenSpec artifact generation, and planning-to-execution handoff expectations.
- Notes: `/change-ready` is intentionally a thin orchestrator; standalone commands remain the source of truth for workflow behavior.

### docs(commands): add standalone next-proposal discovery command
- Summary: Added a dedicated repo-local `/next-proposal` command that evaluates roadmap, backlog, changelog, recent git history, codebase state, and OpenSpec runtime to recommend the next formal proposal without requiring extra context; updated the commands guide to include the new command in the default workflow.
- Why: Proposal discovery is a different decision than choosing the next implementation step, and the existing `/next-step` command was too implementation-oriented for a standalone "what should we propose next?" workflow.
- Files: `.codex/commands/next-proposal.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: Documentation-only change; content reviewed against current command vocabulary, roadmap sequencing, changelog discipline, and OpenSpec workflow expectations.
- Notes: `/next-step` remains unchanged for implementation-step selection; `/next-proposal` is the dedicated entry point for repo-level proposal recommendation.

### feat(data-sync-operations): add local dataset bootstrap and yfinance refresh command workflows
- Summary: Added a new `app/data_sync` orchestration slice and `scripts.data_sync_operations` module CLI with three fail-fast operator commands: `data-bootstrap-dataset1`, `market-refresh-yfinance`, and `data-sync-local`; wired equivalent `just` recipes and fixed invocation to module mode (`uv run python -m scripts.data_sync_operations ...`) so imports resolve deterministically.
- Why: Phase-6 operational execution needed a reproducible local workflow to bootstrap `dataset_1` and refresh market data without introducing a public market-data router, while preserving strict fail-fast stage behavior and auditable run evidence.
- Files: `app/data_sync/{__init__.py,schemas.py,service.py,tests/test_data_sync_operations_cli.py}`, `scripts/data_sync_operations.py`, `justfile`, `app/market_data/providers/yfinance_adapter.py`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{local-workflow-justfile.md,validation-baseline.md,yfinance-integration-guide.md,portfolio-ledger-and-analytics-guide.md}`, `docs/standards/yfance-standard.md`, `CHANGELOG.md`.
- Validation: `uv run ruff check app/data_sync scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py` (pass), `uv run black app/data_sync scripts/data_sync_operations.py app/data_sync/tests/test_data_sync_operations_cli.py --check --diff` (pass), `uv run mypy app/data_sync app/market_data/providers/yfinance_adapter.py app/market_data/service.py` (pass), `uv run pyright app/data_sync app/market_data/providers/yfinance_adapter.py app/market_data/service.py` (0 errors), `uv run ty check app` (pass), `uv run pytest -v app/data_sync/tests/test_data_sync_operations_cli.py app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py` (24 passed), `uv run python -m scripts.data_sync_operations data-sync-local --snapshot-captured-at 2026-03-25T00:00:00Z` (bootstrap stage completed; refresh failed fast with structured `market_refresh` 502 provider error).
- Notes: Public market-data API route and scheduler/queue automation remain deferred; command-level workflows are the active operational boundary in this slice.

### docs(market-data-operations): align phase-6 posture around yfinance operational refresh workflow
- Summary: Updated roadmap, backlog, decisions, validation baseline, provider standard, and yfinance integration guidance to reflect the implemented supported-universe refresh seam (`refresh_yfinance_supported_universe`) as the current operational path, with manual invocation now explicit and schedule infrastructure intentionally deferred.
- Why: Keep planning and implementation artifacts aligned with delivered `app/market_data` behavior and avoid implying broker-authenticated expansion as the immediate next phase-6 step.
- Files: `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md}`, `docs/standards/yfance-standard.md`, `CHANGELOG.md`.
- Validation: `openspec validate add-yfinance-market-data-operations --type change --strict --json` (run during closeout), `openspec validate --specs --all --json` (run during closeout).
- Notes: Non-goals remain explicit: no broker-authenticated provider integration, no multi-provider expansion, no public market-data API expansion, no ledger/canonical mutation, and no valuation KPI/frontend market-value expansion in this slice.

## 2026-03-23

## 2026-03-24

### feat(market-data-provider): add first yfinance adapter with deterministic ingest boundary
- Summary: Added the first external provider adapter under `app/market_data/providers` and a service orchestration path that fetches yfinance day-level close rows, normalizes them to the existing write contract, and persists through the existing idempotent market-data snapshot ingest boundary.
- Why: Phase 6 required proving that external provider data can be ingested without weakening ledger-first truth, non-mutation guarantees, or deterministic validation behavior.
- Files: `app/market_data/providers/{__init__.py,yfinance_adapter.py}`, `app/market_data/service.py`, `app/market_data/tests/{test_yfinance_adapter_unit.py,test_service_unit.py,test_service_integration.py}`, `app/core/config.py`, `app/core/tests/test_config.py`, `pyproject.toml`, `uv.lock`, `docs/product/{roadmap.md,backlog-sprints.md,decisions.md}`, `docs/guides/{validation-baseline.md,yfinance-integration-guide.md}`, `openspec/changes/add-yfinance-market-data-adapter/tasks.md`, `CHANGELOG.md`.
- Validation: `uv run pytest -v app/market_data/tests/test_yfinance_adapter_unit.py app/market_data/tests/test_service_unit.py app/market_data/tests/test_service_integration.py app/core/tests/test_config.py` (23 passed), `uv run ruff check app/market_data/tests/test_service_integration.py` (pass), `uv run pytest -v app/market_data/tests/test_service_integration.py::test_provider_ingest_is_idempotent_and_non_mutating -m integration` (pass), `openspec instructions apply --change add-yfinance-market-data-adapter --json` (progress now 10/13; verification tasks complete).
- Notes: Non-goals remain explicit in this slice: no broker transaction import, no canonical/ledger mutation, no public market-data API expansion, and no valuation KPI expansion.

### docs(yfinance-planning): add provider standard and integration planning guides
- Summary: Added a market-data provider standard plus dedicated yfinance integration and financial-documents guidance to prepare Sprint 5.2 planning with explicit provenance, idempotency, legal, and boundary rules.
- Why: The market-data boundary is implemented, and the next natural step is broker/provider integration; this documentation package reduces scope drift and creates implementation-ready guardrails before coding.
- Files: `docs/standards/yfance-standard.md`, `docs/guides/yfinance-integration-guide.md`, `docs/guides/yfinance-financial-documents-and-fundamentals-guide.md`, `docs/references/references.md`, `docs/README.md`, `docs/product/decisions.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; guidance aligned with current PRD, roadmap, decisions, and market-data boundary contracts.

### docs(external-template-evaluation): assess vstorm ai-agent template and define adoption guardrails
- Summary: Added a formal evaluation note for `vstorm-co/full-stack-ai-agent-template`, updated references and documentation navigation to register it as reference-only material, and proposed an ADR to prevent drop-in template adoption without phase-scoped validation.
- Why: Keep external inspiration useful while preventing scope creep, architecture drift, and premature AI/auth complexity against the current roadmap boundaries.
- Files: `docs/references/full-stack-ai-agent-template-evaluation.md`, `docs/references/references.md`, `docs/README.md`, `docs/product/decisions.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; findings aligned with current PRD, roadmap, and accepted decision constraints.

### docs(market-data-research): add validated ETF yfinance exploration reference note
- Summary: Added a documentation-only ETF exploration note that captures how the local `dashboard_etfs.py` notebook can inform future market-data planning, with explicit boundaries to keep it out of current production scope.
- Why: Preserve useful indicator and ticker research context while avoiding premature provider-integration implementation and keeping roadmap sequencing intact.
- Files: `docs/references/etf-yfinance-research-notes.md`, `docs/references/references.md`, `docs/README.md`, `CHANGELOG.md`.
- Validation: Official sources validated before documentation update (`yfinance` docs/repository legal disclaimer and Yahoo terms links; pandas `pct_change`, `resample`, `ewm` API docs); documentation-only change (no runtime code changes).

### feat(market-data): add isolated ingestion boundary with idempotent snapshot persistence
- Summary: Added a dedicated `app/market_data` slice with `market_data_snapshot` and `price_history` persistence, fail-fast normalization and provenance validation, deterministic symbol/time-key idempotent ingest behavior, and an internal read boundary for symbol price history.
- Why: Establish the first market-data storage boundary required by the roadmap without weakening ledger-first transaction truth or expanding valuation scope prematurely.
- Files: `app/market_data/{models.py,schemas.py,service.py,tests/test_service_unit.py,tests/test_service_integration.py}`, `alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py`, `alembic/env.py`, `docs/product/{roadmap.md,backlog-sprints.md}`, `docs/guides/{validation-baseline.md,portfolio-ledger-and-analytics-guide.md}`, `openspec/changes/add-market-data-ingestion-boundary/{proposal.md,design.md,specs/market-data-ingestion/spec.md,tasks.md}`, `CHANGELOG.md`.
- Validation: `uv run pytest -v app/market_data/tests/test_service_unit.py` (pass), `uv run pytest -v app/market_data/tests/test_service_integration.py -m integration` (pass), `uv run mypy app/market_data` (pass), `uv run ruff check app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py` (pass), `uv run black --check app/market_data alembic/env.py alembic/versions/7d5f2f8f9c3b_add_market_data_storage_scaffold.py` (pass), `uv run alembic upgrade head` (pass), `openspec validate add-market-data-ingestion-boundary --type change --strict --json` (pass).
- Notes: Non-goals remain explicit: no live provider integration, no public market-data API routes, no market-value/unrealized KPI expansion, no FX-rate support, and no frontend market-value UX in this change.

### docs(frontend-evidence): complete hardening evidence bundle for archive readiness
- Summary: Added an automated frontend evidence capture command that generates required release screenshots plus keyboard and accessibility reports, and updated the frontend delivery checklist to link those concrete artifacts.
- Why: The hardening proposal required reproducible evidence for release closeout; strict archive readiness needed screenshot/a11y evidence in addition to CWV metrics.
- Files: `frontend/scripts/capture-frontend-evidence.mjs`, `frontend/package.json`, `docs/evidence/frontend/{accessibility-scan-2026-03-24.md,accessibility-scan-2026-03-24.json,keyboard-walkthrough-2026-03-24.md,keyboard-walkthrough-2026-03-24.json,screenshots-2026-03-24/*}`, `docs/guides/frontend-delivery-checklist.md`, `openspec/changes/add-frontend-hardening-release-evidence/tasks.md`, `CHANGELOG.md`.
- Validation: `npm run build` (pass), `npm run test` (24 passed), `npm run frontend:evidence` (pass), `npm run cwv:measure` (pass; thresholds met).

### fix(frontend-performance): add reproducible CWV harness and resolve summary-route INP regression
- Summary: Added a deterministic CWV measurement harness (`npm run cwv:measure`) using Playwright plus local mock API fixtures, captured baseline and post-fix route metrics, and removed shared panel backdrop blur to reduce interaction rendering cost.
- Why: The hardening change still needed objective CWV evidence for `/portfolio` and `/portfolio/:symbol`; baseline measurement showed summary-route INP above threshold and required a focused optimization before closeout.
- Files: `frontend/scripts/measure-cwv.mjs`, `frontend/package.json`, `frontend/src/app/styles.css`, `docs/evidence/frontend/cwv-report-2026-03-24.md`, `docs/evidence/frontend/cwv-report-2026-03-24T17-11-03.746Z.json`, `docs/evidence/frontend/cwv-report-2026-03-24T17-12-49.067Z.json`, `openspec/changes/add-frontend-hardening-release-evidence/tasks.md`, `CHANGELOG.md`.
- Validation: `npm run cwv:measure` baseline (INP fail on `/portfolio`), targeted CSS optimization, `npm run cwv:measure` post-fix (all thresholds pass), `npm run test` (24 passed), `npm run build` (pass).

### fix(frontend-ui): compact route framing and remove runtime font dependency
- Summary: Replaced the analytics landing-page hero with a compact route frame, shortened route-level copy, promoted the lot-detail return action into the top-level header, removed the runtime Google Fonts import, and added tests that lock the new shell and CSS contracts.
- Why: The accessibility hardening pass was solid, but the shell still felt too editorial for a finance workspace and the runtime font import kept an avoidable dependency in the render path.
- Files: `frontend/src/components/app-shell/AppShell.tsx`, `frontend/src/app/styles.css`, `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.tsx`, `frontend/src/pages/portfolio-lot-detail-page/PortfolioLotDetailPage.tsx`, `frontend/src/components/app-shell/AppShell.test.tsx`, `frontend/src/app/reduced-motion.test.ts`, `CHANGELOG.md`.
- Validation: `npm run test` (24 tests passed); `npm run build` (pass, Vite production bundle generated).
- Notes: At this point in delivery, accessibility scan artifacts were still pending; they were completed later in the `docs(frontend-evidence)` closeout entry on 2026-03-24.

### docs(frontend-hardening): tighten minimalist hierarchy and release-readiness guidance
- Summary: Updated the active frontend hardening OpenSpec change plus frontend architecture/design/checklist/product docs to explicitly require compact workspace-first route hierarchy and production-safe font delivery as part of release readiness.
- Why: Investigation against the current frontend diff and documentation showed that accessibility hardening was progressing, but the shipped guidance still allowed hero-heavy layouts and runtime font loading that weaken professional finance UX and CWV evidence quality.
- Files: `openspec/changes/add-frontend-hardening-release-evidence/{proposal.md,design.md,tasks.md}`, `docs/guides/frontend-architecture-guide.md`, `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-delivery-checklist.md`, `docs/standards/frontend-standard.md`, `docs/product/frontend-mvp-prd-addendum.md`, `CHANGELOG.md`.
- Validation: `git diff --check` (pass); `openspec validate --specs --all --json` (active change valid; unrelated pre-existing spec-format failures remain in `pdf-ingestion` and `pdf-preflight-analysis`).

### feat(frontend-ui): add dual-theme portfolio analytics polish pass and derived overview hierarchy
- Summary: Upgraded the React frontend shell with a user-selectable light/dark theme, stronger semantic design tokens, overview cards for summary and lot-detail screens, row-level drill-down affordances, and more intentional responsive/error-state presentation.
- Why: The initial frontend scaffold matched the documented MVP structure but still felt like a bootstrap pass; this change brings the shipped UI closer to the documented frontend quality bar for Phase 5 without introducing unsupported analytics.
- Files: `frontend/src/app/**`, `frontend/src/components/**`, `frontend/src/features/**`, `frontend/src/pages/**`, `CHANGELOG.md`.
- Validation: `npm run test` (5 tests passed across theme and overview suites), `npm run build` (pass, Vite production bundle generated).

### docs(frontend-ui): align frontend guidance with dual-theme tokens and shipped UX hierarchy
- Summary: Updated the frontend design-system, architecture, delivery checklist, standard, and product addendum to document dual-theme parity requirements, overview-card hierarchy, and the MVP boundary for restrained theme switching.
- Why: The implementation now includes a real theme layer and stronger page composition rules; the docs need to describe those behaviors explicitly so the code and delivery checklists remain aligned.
- Files: `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-architecture-guide.md`, `docs/guides/frontend-delivery-checklist.md`, `docs/standards/frontend-standard.md`, `docs/product/frontend-mvp-prd-addendum.md`, `CHANGELOG.md`.
- Validation: Documentation reviewed against the updated frontend implementation and existing frontend roadmap/quality documents.

### feat(frontend-bootstrap): add React MVP scaffold with typed API boundary and Docker Compose dev service
- Summary: Added the initial `frontend/` application scaffold using React, TypeScript, Vite, React Router, TanStack Query, Zod, and decimal.js, including portfolio summary and lot-detail pages, shared state components, a typed analytics API client, and a Docker Compose frontend dev service.
- Why: Turn the new frontend architecture and UX documentation into an executable MVP foundation so implementation can proceed against the ledger-only analytics contract without inventing structure during delivery.
- Files: `frontend/**`, `docker-compose.yml`, `.env.example`, `.gitignore`, `CHANGELOG.md`.
- Validation: Architecture and API contract reviewed against `docs/guides/frontend-architecture-guide.md`, `docs/guides/frontend-api-and-ux-guide.md`, and `app/portfolio_analytics`; runtime validation executed later in 2026-03-24 frontend UI follow-up (`npm run test`, `npm run build`).

### docs(frontend-architecture): add concrete MVP frontend architecture guide
- Summary: Added a dedicated frontend architecture guide that defines the recommended MVP stack, folder structure, layering model, component boundaries, API boundary strategy, decimal-safe finance handling, and server-state/UI-state testing approach.
- Why: The repository already had frontend product, UX, design-system, and quality documents; this change adds the missing technical bridge between those decisions and executable implementation work.
- Files: `docs/guides/frontend-architecture-guide.md`, `docs/README.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against `docs/product/frontend-mvp-prd-addendum.md`, `docs/guides/frontend-api-and-ux-guide.md`, `docs/guides/frontend-design-system-guide.md`, and `docs/standards/frontend-standard.md`.

### docs(frontend-roadmap): upgrade phase 5 from screen delivery to quality-gated frontend foundation and MVP hardening
- Summary: Expanded the frontend roadmap and sprint backlog so frontend work now explicitly covers design-system foundation, API-to-UI contract locking, decimal-safe finance formatting, accessibility/performance quality gates, and evidence-based release hardening in addition to the summary and lot-detail screens.
- Why: The repository now has a much stronger frontend documentation baseline than the old roadmap reflected; planning needed to catch up so Phase 5 measures real frontend quality instead of only container setup and page existence.
- Files: `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against `docs/product/frontend-mvp-prd-addendum.md`, `docs/guides/frontend-api-and-ux-guide.md`, `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-delivery-checklist.md`, and `docs/standards/frontend-standard.md`.

### feat(portfolio-analytics): add ledger-backed portfolio summary and lot-detail APIs
- Summary: Implemented the new `portfolio_analytics` feature slice with typed response schemas, read-only analytics services derived from persisted ledger truth, and FastAPI routes for grouped summary and lot-detail drill-down.
- Why: Deliver the Phase 4 backend contract required for the frontend MVP while preserving ledger-first, fail-fast analytics boundaries and deferring market-data-dependent valuation.
- Files: `app/portfolio_analytics/{__init__.py,schemas.py,service.py,routes.py,tests/*}`, `app/main.py`, `docs/product/roadmap.md`, `docs/guides/portfolio-ledger-and-analytics-guide.md`, `docs/guides/validation-baseline.md`, `openspec/changes/add-portfolio-analytics-api-from-ledger/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_analytics/tests` (7 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_analytics app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_analytics app/main.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_analytics --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_analytics/service.py app/portfolio_analytics/routes.py app/portfolio_analytics/schemas.py app/main.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run alembic stamp base` + `UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (applied locally for integration-test schema).
- Notes: v1 analytics remain intentionally ledger-only (`open_*`, `realized_*`, `dividend_*`, `as_of_ledger_at`); valuation and unrealized market metrics stay deferred until market-data phases.

### fix(portfolio-ledger): make rebuild state-convergent under canonical corrections and source drift
- Summary: Updated ledger rebuild to clear previously derived lot state before recomputation, upsert derived event rows on canonical-record conflicts, and prune stale derived event rows no longer present in the source document canonical set.
- Why: Ensure `rebuild_portfolio_ledger_from_canonical_records` converges to current canonical truth instead of preserving stale rows from earlier runs.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors).
- Notes: Integration tests for new rebuild regressions could not run in this sandbox because PostgreSQL socket access is blocked (`PermissionError: [Errno 1] Operation not permitted`); run them in a DB-enabled environment.

### fix(docker-local): restore compose defaults compatible with existing postgres_data volumes
- Summary: Switched Docker Compose and `.env.example` defaults back to legacy-compatible `postgres:postgres` credentials while keeping `POSTGRES_APP_*` overrides available for dedicated app-role local setups.
- Why: Prevent local startup breakage for developers with existing `postgres_data` volumes where init scripts do not rerun.
- Files: `docker-compose.yml`, `.env.example`, `CHANGELOG.md`.
- Validation: Configuration update reviewed for variable resolution and compatibility with existing local volume behavior.

### fix(portfolio-ledger): align rebuild convergence with event-type migration and moved-source lot cleanup
- Summary: Changed stale-event pruning to be event-type aware (trade/dividend/split canonical IDs tracked independently) and added a post-upsert lot-state cleanup pass so moved-in transactions do not retain stale lot dispositions.
- Why: Prevent contradictory derived rows when canonical records change event families and ensure lot/disposition truth converges after source-ownership drift corrections.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/portfolio_ledger/tests -m "not integration"` (15 passed, 10 deselected).
- Notes: New integration regressions require a migrated PostgreSQL test database; local run currently fails early with `UndefinedTableError: relation "source_document" does not exist` until `uv run alembic upgrade head` is applied to the active DB.

## 2026-03-22

### docs(roadmap): add deferred database-hardening phase and version-constraint note
- Summary: Updated the roadmap and backlog to state that the current local PostgreSQL baseline uses separated bootstrap and app credentials today while stricter runtime hardening remains deferred until software-version constraints can be revisited.
- Why: Keep planning artifacts aligned with the implemented local baseline and avoid pretending full PostgreSQL hardening is already complete.
- Files: `docs/product/roadmap.md`, `docs/product/backlog-sprints.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against the accepted PostgreSQL security posture and current local runtime constraints.

### docs(database-ops): add local PostgreSQL setup guide and formalize database posture ADR
- Summary: Added a PostgreSQL local setup guide for `.env`, Docker Compose, migrations, and health checks, and recorded the local-first but security-bounded database posture as an accepted ADR.
- Why: Keep local onboarding practical while making the project’s database operating model and security boundary explicit before future hosted or shared environments are introduced.
- Files: `docs/guides/postgres-local-setup.md`, `docs/guides/postgres-security-guide.md`, `docs/product/decisions.md`, `docs/README.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current `.env.example`, `docker-compose.yml`, and the existing PostgreSQL standards and security guides.

### feat(local-postgres): split bootstrap and runtime credentials in Docker local baseline
- Summary: Replaced the insecure `postgres:postgres` local default with explicit admin and app credential variables, mounted a first-boot init script that creates the application role and database, and updated the app container to connect with the dedicated runtime role.
- Why: Align the local baseline with the documented least-privilege direction without making local onboarding impractical.
- Files: `docker-compose.yml`, `.env.example`, `docker/db/init/01-create-app-role.sh`, `docs/guides/postgres-local-setup.md`, `docs/guides/postgres-security-guide.md`, `docs/product/decisions.md`, `CHANGELOG.md`.
- Validation: Configuration review pending runtime verification; expected checks are `docker-compose config`, first-boot database initialization, `uv run alembic upgrade head`, and health endpoint validation.

### docs(database-security): add PostgreSQL security guide and harden database standard
- Summary: Added a dedicated PostgreSQL security guide and expanded the PostgreSQL standard with security baseline rules covering authentication, least-privilege roles, network exposure, TLS expectations, privilege hygiene, and security-sensitive features.
- Why: The repository already documented application-code security with Bandit, but lacked a database-specific security posture for PostgreSQL setup and future shared or remote environments.
- Files: `docs/guides/postgres-security-guide.md`, `docs/standards/postgres-standard.md`, `docs/README.md`, `docs/references/references.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current PostgreSQL 18 documentation plus the provided Tiger Data security references, with PostgreSQL 7.0 explicitly treated as historical unsupported context.

### docs(database): add PostgreSQL standard and optional extension guides
- Summary: Added a repository PostgreSQL standard plus focused guides for performance investigation, `pgvector`, and TimescaleDB adoption, and linked them from the main documentation indexes and references.
- Why: Formalize how database schema, migrations, indexing, and extension choices should be handled without mixing core PostgreSQL rules with optional future features.
- Files: `docs/standards/postgres-standard.md`, `docs/guides/postgres-performance-guide.md`, `docs/guides/pgvector-guide.md`, `docs/guides/timescaledb-guide.md`, `docs/README.md`, `docs/references/references.md`, `README.md`, `CHANGELOG.md`.
- Validation: Documentation-only update; content reviewed against current repository schema/query patterns and official PostgreSQL, `pgvector`, and Tiger Data documentation.

### feat(portfolio-ledger): close phase 3 ledger foundation and accounting-policy freeze for dataset 1
- Summary: Completed ledger-foundation closeout by fixing fractional lot-basis precision propagation, finalizing strict typing/lint compliance in ledger tests, and adding a fractional buy/sell integration regression for cent-consistent FIFO basis behavior.
- Why: Lock a trustworthy, explicit portfolio-ledger and accounting-policy contract before Phase 4 analytics APIs and frontend work.
- Files: `app/portfolio_ledger/{service.py,accounting.py,schemas.py,tests/test_policy_schemas.py,tests/test_rebuild_integration.py,tests/test_canonical_mapping.py,tests/test_models_schema.py,tests/test_fifo_accounting.py,tests/fixtures/dataset_1_v1_finance_cases.json}`, `docs/product/roadmap.md`, `docs/guides/portfolio-ledger-and-analytics-guide.md`, `docs/guides/validation-baseline.md`, `openspec/changes/add-ledger-foundation-and-accounting-policy-for-dataset-1/tasks.md`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 3 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (3 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_ledger --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger` (pass), `openspec validate --specs --all` (this change passes; pre-existing failures remain in `spec/pdf-ingestion` and `spec/pdf-preflight-analysis`).
- Notes: Product and guide docs now explicitly record that Phase 3 is ledger/accounting foundation only; market-data valuation and analytics endpoints remain deferred to later phases.

### fix(portfolio-ledger): preserve residual lot basis cents across partial sells and correct open-lot summary count
- Summary: Updated sell-side lot mutation logic to carry remaining lot basis by subtraction (with close-lot residual allocation) instead of recomputing from unit basis, and changed rebuild summary `open_lots` to count only lots with positive remaining quantity.
- Why: Prevent realized-basis drift from repeating-decimal unit costs and keep rebuild/log output semantically accurate for open positions.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_fractional_three_partial_sells_preserves_basis_and_open_lot_count` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 4 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (4 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(portfolio-ledger): order same-day lot events by canonical sequence across split and trade records
- Summary: Replaced the hard-coded same-day trade-before-split lot event ordering with canonical-record ordering so same-day split/trade histories are applied in persisted canonical order.
- Why: Prevent false FIFO insufficient-lot failures and miscomputed lot state when a same-day split must precede a same-day sell.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_same_day_split_before_sell_uses_canonical_event_order` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (5 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 5 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(portfolio-ledger): enforce explicit rebuild transactions after session autobegin
- Summary: Updated rebuild transaction handling to clear implicit `AUTOBEGIN` state before ledger writes and always run writes inside an explicit `begin()` or `begin_nested()` scope, with an integration regression for pre-read/autobegin sessions.
- Why: Prevent rebuild persistence from depending on unrelated prior session reads and guarantee local commit/rollback ownership for the rebuild path.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py::test_rebuild_autobegin_session_still_commits_ledger_writes` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (6 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (14 passed, 6 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger/service.py app/portfolio_ledger/tests/test_rebuild_integration.py` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger/service.py` (pass).

### fix(validation): clear pyright unknown-type route helper and restore black formatting gate
- Summary: Added explicit JSON payload narrowing in the persistence route test helper and restored Black-compliant spacing in the persistence schema migration module.
- Why: Close repository validation failures (`pyright app/` unknown member/type usage and `black --check` formatting drift) without changing runtime behavior.
- Files: `app/pdf_persistence/tests/test_routes.py`, `alembic/versions/c8b0721b0977_add_pdf_persistence_schema.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run black . --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check .` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app` (pass).

### fix(portfolio-ledger): isolate implicit session transactions and reject non-finite canonical decimals
- Summary: Replaced the rebuild path’s implicit-transaction rollback with an isolated-session execution path for `AUTOBEGIN` state (preserving caller transaction state), and tightened canonical decimal coercion to reject non-finite values (`NaN`, `Infinity`, `-Infinity`) with deterministic 422 errors.
- Why: Prevent silent caller transaction mutation/data loss while keeping duplicate-safe reruns functional, and enforce finance-safe numeric semantics before lot math executes.
- Files: `app/portfolio_ledger/service.py`, `app/portfolio_ledger/tests/test_rebuild_integration.py`, `app/portfolio_ledger/tests/test_canonical_mapping.py`, `CHANGELOG.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run alembic upgrade head` (pass after local schema reset), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v app/portfolio_ledger/tests -m "not integration"` (15 passed, 6 deselected), `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -v -m integration app/portfolio_ledger/tests/test_rebuild_integration.py` (6 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/portfolio_ledger alembic/env.py alembic/versions/12ecb9689094_add_portfolio_ledger_foundation_tables.py` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run black app/portfolio_ledger alembic/env.py alembic/versions/12ecb9689094_add_portfolio_ledger_foundation_tables.py --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run bandit -c pyproject.toml -r app/portfolio_ledger --severity-level high --confidence-level high` (no issues), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/portfolio_ledger` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/portfolio_ledger` (0 errors), `UV_CACHE_DIR=/tmp/uv-cache uv run ty check app/portfolio_ledger` (pass).

## 2026-03-21

### feat(pdf-persistence): persist canonical dataset 1 records in PostgreSQL with duplicate-safe reruns
- Summary: Implemented `pdf_persistence` end-to-end with transactional source-document reuse/create, success-only `import_job` auditing, and canonical-record insert-or-skip behavior keyed by deterministic versioned fingerprints.
- Why: Complete the persistence boundary required before ledger modeling and analytics phases while preserving fail-fast behavior and rerun safety.
- Files: `app/pdf_persistence/{models.py,schemas.py,service.py,routes.py,tests/test_*.py}`, `alembic/versions/c8b0721b0977_add_pdf_persistence_schema.py`, `app/main.py`, `openspec/changes/add-postgres-persistence-for-canonical-pdf-records/tasks.md`.
- Validation: `UV_CACHE_DIR=/tmp/uv uv run alembic upgrade head` (pass), `UV_CACHE_DIR=/tmp/uv uv run pytest -v app/pdf_persistence/tests` (13 passed), `UV_CACHE_DIR=/tmp/uv uv run pytest -v -m integration` (14 passed, 111 deselected), `UV_CACHE_DIR=/tmp/uv uv run mypy app/` (pass), `UV_CACHE_DIR=/tmp/uv uv run pyright app/` (0 errors), `UV_CACHE_DIR=/tmp/uv uv run ty check app` (pass), `UV_CACHE_DIR=/tmp/uv uv run ruff check .` (pass), `UV_CACHE_DIR=/tmp/uv uv run black . --check --diff` (pass), `UV_CACHE_DIR=/tmp/uv uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` (no issues).
- Notes: Replay for this phase remains dependent on stored PDFs plus ingestion metadata manifests; v1 multi-source reconciliation remains deferred by design.

### docs(guides): update persistence reference guidance after 2.x-4.1 completion
- Summary: Updated baseline and extraction/golden-set guides to reflect implemented persistence behavior, including duplicate-safe reprocessing, success-only `import_job` rows, and replay/source-of-truth boundaries.
- Why: Remove stale guidance that still marked persistence as pending and make the implemented contract explicit for operators and AI agents.
- Files: `docs/guides/validation-baseline.md`, `docs/guides/pdf-extraction-guide.md`, `docs/guides/golden-set-contract.md`, `CHANGELOG.md`.
- Validation: `openspec validate --specs --all --json` confirms this change validates; existing unrelated spec-format failures remain in `spec/pdf-ingestion` and `spec/pdf-preflight-analysis` (missing required `## Purpose`/`## Requirements` sections).
- Notes: The pre-existing OpenSpec spec-validation issue remains unresolved and should be handled in a separate documentation/spec-format cleanup change.

### docs(commands): make commit-local force single all-in local commit
- Summary: Updated `.codex/commands/commit-local.md` to always stage full working tree (`git add -A`) and create one local commit, even when scope is mixed, while still stopping before any push.
- Why: Align command behavior with user expectation for an explicit all-in local packaging command.
- Files: `.codex/commands/commit-local.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: Reviewed command workflow and guardrails to confirm mixed scope no longer blocks commit-local execution.

### docs(commands): add local-only commit-local command
- Summary: Added `.codex/commands/commit-local.md` as a local-only companion to `/commit` that reviews staged, unstaged, and untracked work, stages the full intended tree, generates a descriptive commit message, creates the commit, and stops before any push.
- Why: Support the preferred workflow where commit creation can be automated locally while the final `git push` remains a separate manual user action.
- Files: `.codex/commands/commit-local.md`, `.codex/commands/README.md`, `CHANGELOG.md`.
- Validation: Reviewed command-index alignment and confirmed `commit-local` is listed in `.codex/commands/README.md`.

### docs(structure): reorganize repository documentation into product guides standards and references
- Summary: Reordered `docs/` into `product/`, `guides/`, `standards/`, and `references/`, moved all `*-standard.md` files into one shared `docs/standards/` directory, and added `docs/README.md` as the navigation index.
- Why: Reduce root-level clutter, make standards discoverable in one canonical location, and keep product, guide, and reference material clearly separated as the documentation set grows.
- Files: `docs/README.md`, `docs/product/*`, `docs/guides/*`, `docs/standards/*`, `docs/references/references.md`, `README.md`, `AGENTS.md`, `openspec/project.md`, `app/core/logging.py`, archived OpenSpec task notes, `CHANGELOG.md`.
- Validation: `rg -n "docs/(ruff-standard|black-standard|bandit-standard|mypy-standard|pyright-standard|pytest-standard|ty-standard|logging-standard|prd\.md|roadmap\.md|decisions\.md|references\.md|backlog-sprints\.md|reference-guides/)"` returned no remaining stale references.

### chore(validation): add Black and Bandit as first-class validation gates
- Summary: Added `ty` as an additional required type-check gate, raised Bandit gate thresholds to `high/high`, and propagated the updated baseline across governance/docs/command matrices.
- Why: Tighten security threshold policy and strengthen static typing coverage while keeping validation commands explicit and reproducible for both humans and AI agents.
- Files: `pyproject.toml`, `uv.lock`, `AGENTS.md`, `README.md`, `docs/standards/ty-standard.md`, `docs/standards/bandit-standard.md`, `docs/standards/black-standard.md`, `docs/guides/validation-baseline.md`, `docs/references/references.md`, `docs/product/backlog-sprints.md`, `.codex/commands/{README.md,plan.md,execute.md,validate.md}`, `openspec/changes/add-postgres-persistence-for-canonical-pdf-records/tasks.md`, `CHANGELOG.md`.
- Validation: `uv run ruff check .` (pass), `uv run black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (pass), `uv run ty check app` (pass), `uv run pytest -v -m "not integration"` (pass), `uv run pytest -v -m integration` (pass).

## 2026-03-19

### feat(pdf-ingestion): persist durable upload metadata manifests beside stored PDFs
- Summary: Updated PDF ingestion to write a JSON sidecar manifest for each stored upload and added a loader that recovers durable ingestion metadata from `storage_key` for later persistence work.
- Why: Lift the persistence-planning blocker where `storage_key` alone could not recover fields such as original filename, content type, file size, SHA-256, and page count after the initial upload response was gone.
- Files: `app/pdf_ingestion/service.py`, `app/pdf_ingestion/tests/test_service.py`, `app/pdf_ingestion/tests/test_routes.py`.
- Validation: `UV_CACHE_DIR=/tmp/uv-cache uv run pytest -q app/pdf_ingestion/tests` (12 passed), `UV_CACHE_DIR=/tmp/uv-cache uv run mypy app/pdf_ingestion` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run ruff check app/pdf_ingestion` (pass), `UV_CACHE_DIR=/tmp/uv-cache uv run pyright app/pdf_ingestion` (0 errors).
- Notes: `uv run black ... --check` remained blocked in the sandbox because Black attempted to open a multiprocessing listener socket; formatting was not auto-verified through the Black gate in this session.

### feat(pdf-canonical): add dataset 1 canonical normalization and verification slices
- Summary: Implemented `pdf_normalization` and `pdf_verification` service/route slices to convert extracted dataset 1 rows into typed canonical records and produce deterministic mismatch reports against the checked-in golden contract.
- Why: Freeze trusted canonical contracts and verification evidence before starting PostgreSQL persistence and deduplication work.
- Files: `app/pdf_normalization/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/pdf_verification/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/main.py`, `openspec/changes/add-dataset-1-canonical-normalization-and-verification/tasks.md`.
- Validation: `uv run pytest -v app/pdf_normalization/tests app/pdf_verification/tests` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass), `uv run black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (no issues).
- Notes: Verification record pairing now uses deterministic fallback identity (`table_name` + `row_index` + `source_page`) so `splits` rows reconcile even when golden rows omit `row_id`.

### docs(reference-guides): record canonical baseline completion and persistence boundary
- Summary: Updated extraction and validation reference guides to reflect that extraction, normalization, and verification are implemented for dataset 1 while persistence remains pending.
- Why: Keep operational docs aligned with delivered behavior and avoid stale guidance that still marks canonical processing as unimplemented.
- Files: `docs/guides/pdf-extraction-guide.md`, `docs/guides/validation-baseline.md`.
- Validation: Documentation reviewed against current `app/pdf_extraction`, `app/pdf_normalization`, `app/pdf_verification` implementations and task checklist status.

## 2026-03-18

### chore(validation): integrate Black and Bandit as required baseline gates
- Summary: Added Black and Bandit as first-class validation layers in tooling/config and propagated the baseline command set across repo guidance and command docs.
- Why: Ensure formatting and security scanning are enforced consistently alongside Ruff, MyPy, Pyright, and pytest rather than remaining documentation-only guidance.
- Files: `pyproject.toml`, `uv.lock`, `.python-version`, `.codex/commands/{README.md,plan.md,execute.md,validate.md}`, `AGENTS.md`, `README.md`, `docs/guides/validation-baseline.md`, `docs/standards/ruff-standard.md`, `docs/standards/black-standard.md`, `docs/product/backlog-sprints.md`, `app/main.py`.
- Validation: `uv run ruff check .` (pass), `uv run --python 3.12.6 black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (pass), `uv run pytest -q` (100 passed).
- Notes: Added scoped `# nosec B104` on intentional dev bind in `app/main.py` to align Bandit with existing `# noqa: S104` policy.

### docs(quality-gates): add Black and Bandit standards for validation and security
- Summary: Added dedicated standards documentation for Black and Bandit, including configuration baselines, command usage, gate policy, and integration guidance with existing Ruff/MyPy/Pyright/Pytest workflow.
- Why: Formalize how to adopt Black and Bandit in a controlled way using official tooling guidance while keeping repository validation rules explicit and reproducible.
- Files: `docs/standards/black-standard.md`, `docs/standards/bandit-standard.md`, `docs/references/references.md`, `README.md`.
- Validation: Documentation-only update; content reviewed against official Black and Bandit docs and current repository validation structure.

### feat(pdf_extraction): add deterministic pdfplumber extraction from stored uploads
- Summary: Implemented `app/pdf_extraction` service and `/api/pdf/extract` route to parse dataset 1 tables from stored PDFs with deterministic row order, provenance, and explicit header/footer filtering.
- Why: Complete Sprint 1 Item 1.3 extraction slice before normalization/persistence work.
- Files: `app/pdf_extraction/service.py`, `app/pdf_extraction/routes.py`, `app/pdf_extraction/schemas.py`, `app/pdf_extraction/tests/test_service.py`, `app/pdf_extraction/tests/test_routes.py`, `app/main.py`, `pyproject.toml`, `docs/guides/pdf-extraction-guide.md`.
- Validation: `uv run pytest -v app/pdf_extraction/tests` (6 passed), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass).
- Notes: Current scope is raw extraction only; canonical mapping/normalization and persistence remain out of scope for this slice.

## 2026-04-18

### docs(frontend): harden compact dashboard proposal with frontend engineering gates
- Summary: Refined the compact dashboard OpenSpec change to make component architecture, accessibility, responsive behavior, semantic token usage, and meaningful UI state handling explicit implementation requirements.
- Why: The proposal was visually and analytically strong, but still under-specified on production-grade frontend engineering constraints needed before implementation.
- Files: `openspec/changes/archive-v0-and-build-compact-trading-dashboard/{proposal.md,design.md,tasks.md,specs/frontend-compact-trading-dashboard/spec.md}`.
- Validation: `rtk openspec validate "archive-v0-and-build-compact-trading-dashboard" --type change --strict --json`.

## 2026-03-17

### docs(commands): require explicit blast-radius and blind-spot diagnosis in /plan
- Summary: Tightened `/plan` so planning must explicitly diagnose blast radius and blind spots, and must state whether `CHANGELOG.md` updates are required.
- Why: Reduce hidden planning risk and make downstream contract propagation visible before implementation starts.
- Files: `.codex/commands/plan.md`, `.codex/commands/README.md`.
- Validation: Documentation review against current planning workflow and repo governance rules.

### docs(commands): overhaul OpenSpec command workflow and add /explain
- Summary: Reworked command docs for `/prime`, `/plan`, `/execute`; added `/explain`; synchronized command README.
- Why: Improve execution control, planning rigor, and repo-fit guidance for AI-assisted workflow.
- Files: `.codex/commands/prime.md`, `.codex/commands/plan.md`, `.codex/commands/execute.md`, `.codex/commands/explain.md`, `.codex/commands/README.md`.
- Validation: Documentation-only change; reviewed command coverage and examples.

## 2026-03-08

### docs: refine Codex command workflow guidance
- Summary: Updated command-layer documentation and workflow guidance.
- Why: Improve consistency and operator clarity.
- Files: Command docs and related guidance files.
- Validation: Documentation review.

### feat(pdf_ingestion): add PDF ingestion endpoint with preflight and local storage
- Summary: Added PDF ingestion flow with preflight validation and local storage behavior.
- Why: Enable end-to-end upload and preflight path for PDF workflows.
- Files: `app/pdf_ingestion/*`, routing/config/tests.
- Validation: Change tasks completed in OpenSpec; validation executed in implementation flow.

### feat(pdf_preflight): add PDF preflight analysis endpoint
- Summary: Introduced API support for PDF preflight analysis.
- Why: Provide validation and metadata extraction before downstream processing.
- Files: PDF preflight feature modules and tests.
- Validation: Feature validation executed during implementation cycle.

### feat(workflow): add Codex workflow commands and approval-gated commit flow
- Summary: Added repo-local command workflow for prime/plan/execute/validate/commit.
- Why: Standardize AI-assisted delivery process and approval checkpoints.
- Files: `.codex/commands/*`.
- Validation: Command documentation and flow checks.
