## 1. Investigation and baselining

- [x] 1.1 Confirm hardening scope against roadmap, frontend addendum, frontend standard, and delivery checklist
Notes: Reviewed `docs/product/roadmap.md` (Phase 5), `docs/product/frontend-mvp-prd-addendum.md`, `docs/standards/frontend-standard.md`, and `docs/guides/frontend-delivery-checklist.md`; all align on hardening-first scope and explicitly defer market-value/FX expansion.
Notes: Confirmed release gates remain evidence-driven: explicit state reliability (`loading`, `empty`, `404`, `422`, `500`), WCAG 2.2 AA baseline checks, and CWV evidence before release readiness closeout.
- [x] 1.2 Capture current frontend validation baseline (`npm run test`, `npm run build`) and identify failing/blocked quality gates
Notes: Task-local proof on 2026-03-24: `npm run test` PASS (`3` files, `5` tests).
Notes: Task-local proof on 2026-03-24: `npm run build` PASS (`tsc -b` + `vite build`; production bundle emitted under `frontend/dist/`).
Notes: Current blocked quality gates are evidence-only gates from Phase 5/6 (accessibility scan report + CWV report), pending audit tooling and executable browser availability.
- [x] 1.3 Diagnose accessibility and performance audit tooling paths available in local environment and document blockers
Notes: Tooling inventory: `npm run` exposes only `dev`, `test`, `build`, and `preview`; there are no dedicated `a11y`, `e2e`, or `perf` scripts yet.
Notes: `playwright@1.58.2` CLI is available, but browser executables are missing at Playwright cache paths (`chromium`, `firefox`, `webkit`), so browser-driven audits are blocked until browser binaries are installed.
Notes: No `playwright.config.*`, no `e2e` test files, and no `lighthouse` or `axe-core` packages configured; `npx lighthouse` / `npx @axe-core/cli` do not complete in current restricted-network sandbox, so WCAG/CWV artifact capture is blocked locally until tooling is added and dependency fetch is available.
- [x] 1.4 Audit route-level visual hierarchy and asset-delivery risks against the documented frontend design system
Notes: The current `AppShell` hero pattern is visually polished but too editorial for a finance workspace hardening pass; duplicated explainer cards compete with timestamp/scope/data context instead of reinforcing it.
Notes: `frontend/src/app/styles.css` currently imports Google Fonts via runtime `@import`, which conflicts with the documented preference for self-hosted/preloaded `woff2` delivery and should be treated as a release-readiness risk for CWV evidence.

## 2. State reliability and test coverage

- [x] 2.1 Add or extend tests for summary and lot-detail success/empty/error/not-found state mapping
Notes: Added page-level state mapping coverage in `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.test.tsx` and `frontend/src/pages/portfolio-lot-detail-page/PortfolioLotDetailPage.test.tsx` for loading, empty, explicit error, and not-found flows.
Notes: Summary tests now assert explicit error rendering with API detail propagation and retry affordance; lot-detail tests now assert dedicated not-found warning behavior without degrading to empty-success rendering.
- [x] 2.2 Add coverage for retry/back navigation behavior and deterministic symbol handling from route params
Notes: Added interaction assertions for retry buttons and summary/back navigation links in both page-level test suites (`Retry request`, `Back to summary`, `Return to grouped summary`).
Notes: Implemented deterministic route-param normalization in `frontend/src/pages/portfolio-lot-detail-page/PortfolioLotDetailPage.tsx` (`trim + uppercase`) and locked behavior with route test coverage for `/portfolio/%20voo%20` -> `VOO`.
- [x] 2.3 Ensure theme preference behavior remains covered and stable under state transitions
Notes: Added a summary-page transition test that toggles theme, transitions query state (`loading` -> `error`), and verifies `document.documentElement.dataset.theme` plus localStorage theme persistence remain stable across rerenders.
Notes: Existing pure preference-resolution tests in `frontend/src/app/theme.test.ts` remain in place and now complement component-level transition coverage.

## 3. Accessibility hardening

- [x] 3.1 Run keyboard/focus walkthrough for core screens and patch interaction issues
Notes: Keyboard/focus walkthrough of core summary and lot-detail actions confirmed operable controls for theme toggle, retry/back links, and summary row drill-down; the primary gap was weak dedicated focus treatment on interactive summary table rows.
Notes: Patched interactive row focus styling in `frontend/src/app/styles.css` with explicit focus-visible background + ring treatment and clearer focused call-to-action emphasis for keyboard users.
Notes: Added keyboard navigation coverage in `frontend/src/features/portfolio-summary/PortfolioSummaryTable.keyboard.test.tsx` to prove row focusability and Enter/Space activation of lot-detail navigation.
- [x] 3.2 Run contrast checks in light and dark themes and patch token/component regressions
Notes: Ran deterministic contrast checks for core text and status/badge token pairs in light and dark themes; light-theme regressions were found for muted body text and accent/warning text over soft badge backgrounds.
Notes: Patched light-theme token values in `frontend/src/app/styles.css` (`--color-text-muted`, `--color-accent`, `--color-warning`) to restore AA-oriented contrast headroom while preserving existing semantic color meaning.
Notes: Added token-level contrast regression coverage in `frontend/src/app/contrast.test.ts` to enforce minimum ratio checks for key pairs in both themes and prevent future drift.
- [x] 3.3 Validate reduced-motion behavior and semantic labeling for core interactive controls
Notes: Validated reduced-motion behavior by enforcing a test-backed CSS contract in `frontend/src/app/reduced-motion.test.ts` for the `@media (prefers-reduced-motion: reduce)` rule that disables animations/transitions globally.
Notes: Improved semantic error-state behavior in `frontend/src/components/error-banner/ErrorBanner.tsx` by setting variant-aware live-region roles (`alert`/`status`) and labeling via `aria-labelledby` for reliable accessible naming.
Notes: Added explicit keyboard shortcut metadata (`aria-keyshortcuts=\"Enter Space\"`) on interactive summary rows and locked semantic behavior with targeted tests in `frontend/src/components/error-banner/ErrorBanner.a11y.test.tsx` and `frontend/src/features/portfolio-summary/PortfolioSummaryTable.keyboard.test.tsx`.

## 4. Performance hardening

- [x] 4.1 Capture CWV-oriented measurements (LCP, INP, CLS) for `/portfolio` and `/portfolio/:symbol`
Notes: Added reproducible CWV measurement tooling in `frontend/scripts/measure-cwv.mjs` plus `npm run cwv:measure` script entry in `frontend/package.json`, using Playwright + deterministic local API fixtures for `/portfolio` and `/portfolio/VOO`.
Notes: Initial CWV capture (`docs/evidence/frontend/cwv-report-2026-03-24T17-11-03.746Z.json`) found a summary-route INP regression (`232ms` p75) while LCP/CLS remained well within thresholds.
- [x] 4.2 Implement targeted optimizations for any threshold regressions without expanding feature scope
Notes: Applied targeted rendering-cost optimization in `frontend/src/app/styles.css` by removing panel backdrop blur compositing from the shared `.panel` primitive, keeping visual direction while reducing interaction overhead on global theme updates.
- [x] 4.2.1 Remove runtime third-party font stylesheet dependency for core typography or document a justified, validated fallback before final CWV sign-off
Notes: Removed the runtime Google Fonts `@import` from `frontend/src/app/styles.css` and kept the documented local/system fallback stack so production builds no longer depend on third-party stylesheet fetches for primary typography.
Notes: Added a CSS contract assertion in `frontend/src/app/reduced-motion.test.ts` to prevent reintroducing runtime stylesheet imports for primary fonts.
- [x] 4.2.2 Reduce above-the-fold shell weight if route-level framing delays access to timestamp, scope note, or primary drill-down workflow on standard laptop widths
Notes: Replaced the editorial two-column hero in `frontend/src/components/app-shell/AppShell.tsx` with a compact route frame that keeps title, scope note, and route action visible without stacked explainer cards.
Notes: Shortened route-level copy in `frontend/src/pages/portfolio-summary-page/PortfolioSummaryPage.tsx` and `frontend/src/pages/portfolio-lot-detail-page/PortfolioLotDetailPage.tsx`, and added `frontend/src/components/app-shell/AppShell.test.tsx` to lock the compact framing behavior.
- [x] 4.3 Re-measure and confirm post-fix performance outcomes
Notes: Post-fix CWV capture (`docs/evidence/frontend/cwv-report-2026-03-24T17-12-49.067Z.json`) passes thresholds on both routes: `/portfolio` (`LCP 296ms`, `INP 96ms`, `CLS 0`) and `/portfolio/VOO` (`LCP 284ms`, `INP 88ms`, `CLS 0`).
Notes: Added consolidated evidence summary in `docs/evidence/frontend/cwv-report-2026-03-24.md`, including pre-fix to post-fix delta and capture methodology.

## 5. Evidence and documentation closeout

- [x] 5.1 Update frontend delivery checklist and design guidance with completed evidence references plus any finalized hierarchy/font-delivery rules
Notes: Updated `docs/guides/frontend-delivery-checklist.md`, `docs/guides/frontend-design-system-guide.md`, `docs/guides/frontend-architecture-guide.md`, `docs/standards/frontend-standard.md`, and `docs/product/frontend-mvp-prd-addendum.md` to make compact workspace hierarchy and production-safe font delivery explicit release requirements.
- [x] 5.2 Update changelog and related frontend docs with hardening outcomes and known limitations
Notes: Added changelog entries documenting both the guidance update and the implemented frontend hardening pass.
Notes: Follow-up closeout added deterministic evidence capture via `npm run frontend:evidence`, producing screenshot, keyboard-walkthrough, and accessibility-scan artifacts without introducing new third-party runtime dependencies.
- [x] 5.3 Run final frontend validation pass and record PASS/PARTIAL PASS with explicit blockers
Notes: Final frontend validation on 2026-03-24: `npm run test` PASS (`10` files, `24` tests); `npm run build` PASS (Vite production bundle emitted under `frontend/dist/`); `npm run cwv:measure` PASS after targeted INP optimization; `npm run frontend:evidence` PASS (artifacts generated under `docs/evidence/frontend/`).
Notes: `openspec validate --specs --all --json` still reports unrelated pre-existing spec-format failures in `pdf-ingestion` and `pdf-preflight-analysis`; the active frontend hardening change validates successfully.
