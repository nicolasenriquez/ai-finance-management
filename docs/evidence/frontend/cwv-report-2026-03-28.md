# Frontend CWV Evidence - 2026-03-28

## Method

- Tooling: Playwright + `PerformanceObserver` harness (`npm --prefix frontend run cwv:measure`)
- Runs per route: `5`
- Thresholds: `LCP <= 2500ms`, `INP <= 200ms`, `CLS <= 0.1` (p75)
- Raw JSON: `docs/evidence/frontend/cwv-report-2026-03-28T04-35-40.732Z.json`

## Route Results (p75)

| Route | LCP (ms) | INP (ms) | CLS | Verdict |
| --- | ---: | ---: | ---: | --- |
| `/portfolio` | 380 | 80 | 0.0000 | PASS |
| `/portfolio/VOO` | 364 | 80 | 0.0000 | PASS |
| `/portfolio/home?period=30D` | 396 | 88 | 0.0098 | PASS |
| `/portfolio/analytics?period=90D` | 416 | 96 | 0.0012 | PASS |
| `/portfolio/risk?period=252D` | 380 | 80 | 0.0012 | PASS |
| `/portfolio/transactions` | 412 | 96 | 0.0010 | PASS |

## Summary

- Overall verdict: `PASS` across all measured routes.
- Workspace routes (`home`, `analytics`, `risk`, `transactions`) remain comfortably below CWV thresholds.
