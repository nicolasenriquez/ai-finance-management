# Phase P Dashboard Baseline Evidence

Change: `phase-p-dashboard-saas-hardening-before-dca`
Date: `2026-04-18`

## Objective

Capture pre-refactor baseline evidence for compact-route first-surface readiness before route-level orchestration and chart-realization work.

## Command Evidence

Executed:

```bash
rtk npm run test -- \
  src/pages/portfolio-home-page/PortfolioHomePage.contract.test.tsx \
  src/pages/portfolio-analytics-page/PortfolioAnalyticsPage.contract.test.tsx \
  src/pages/portfolio-risk-page/PortfolioRiskPage.contract.test.tsx \
  src/pages/portfolio-signals-page/PortfolioSignalsPage.contract.test.tsx
```

Result:
- 4/4 route contract files passed.
- Total duration: `12.71s`.

Per-route test timings from Vitest output:

| Route contract test | Time |
| --- | --- |
| `PortfolioHomePage.contract.test.tsx` | `695ms` |
| `PortfolioAnalyticsPage.contract.test.tsx` | `1271ms` |
| `PortfolioRiskPage.contract.test.tsx` | `1021ms` |
| `PortfolioSignalsPage.contract.test.tsx` | `1292ms` |

## First-Surface Request Baseline (Static Inventory)

Current pre-refactor first-surface dependencies:

| Route | Current first-surface sources |
| --- | --- |
| `/portfolio/home` | `summary`, `command-center`, `hierarchy` |
| `/portfolio/analytics` | `summary`, `hierarchy`, `contribution` |
| `/portfolio/risk` | `summary`, `command-center` |
| `/portfolio/signals` | `summary`, `hierarchy` |

Observation baseline:
- Home and Risk are missing first-surface `time-series` fetch ownership for chart-first rendering.
- Analytics and Risk still rely on pseudo/static first-surface visual modules.
- Signals still includes static trend-regime summary rows.

## Fail-First Contract Baseline

Executed:

```bash
rtk npm run test -- src/app/route-performance-orchestration.contract.fail-first.test.ts
```

Result:
- Fails as expected on orchestration contract:
  - missing dedicated risk route hook and query ownership contract (`usePortfolioRiskRouteData.ts` not present).
- Passes opportunities mapping check:
  - `Opportunities` label remains mapped to `/portfolio/signals`.

This baseline is the unlock point for Stage 2 refactor.

## Post-Hardening Evidence

Date: `2026-04-18`

### Command Evidence

Executed:

```bash
rtk npm --prefix frontend run test
rtk npm --prefix frontend run lint
rtk npm --prefix frontend run build
rtk openspec validate phase-p-dashboard-saas-hardening-before-dca --type change --strict --json
rtk openspec validate --specs --all --json
```

Result:
- `frontend test`: pass (`25/25` files, `50/50` tests, duration `58.81s`).
- `frontend lint`: pass (`tsc --noEmit` app/node configs).
- `frontend build`: pass (`vite build`, duration `12.43s`).
- `openspec validate` change strict: pass (`valid: true`, no issues).
- `openspec validate --specs --all`: pass (`33/33` items valid, no issues).

Per-route contract timings from post-hardening full-suite run:

| Route contract test | Time |
| --- | --- |
| `PortfolioHomePage.contract.test.tsx` | `861ms` |
| `PortfolioAnalyticsPage.contract.test.tsx` | `733ms` |
| `PortfolioRiskPage.contract.test.tsx` | `2115ms` |
| `PortfolioSignalsPage.contract.test.tsx` | `1538ms` |

### Before/After Readout

| Route contract test | Baseline (pre-hardening) | Post-hardening |
| --- | --- | --- |
| `PortfolioHomePage.contract.test.tsx` | `695ms` | `861ms` |
| `PortfolioAnalyticsPage.contract.test.tsx` | `1271ms` | `733ms` |
| `PortfolioRiskPage.contract.test.tsx` | `1021ms` | `2115ms` |
| `PortfolioSignalsPage.contract.test.tsx` | `1292ms` | `1538ms` |

Interpretation:
- Analytics improved in contract runtime after orchestration and chart realization.
- Risk and Signals increased due to richer first-surface modules and deeper contract-backed rendering.
- Gate quality remains green with deterministic async-state behavior and strict OpenSpec validation.

### Environment Notes

- Recharts emits JSDOM warnings during tests (`width(-1) and height(-1)`), but tests and build remain green.
- These warnings are non-blocking for this change; runtime chart rendering in app containers remains stable.

### Handoff Note

Phase P hardening is complete for the compact dashboard baseline.
DCA workflow implementation is explicitly next and remains out of scope for this phase.
