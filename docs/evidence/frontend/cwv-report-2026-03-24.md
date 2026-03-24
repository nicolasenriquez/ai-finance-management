# Frontend CWV Evidence - 2026-03-24

## Scope

- Routes measured: `/portfolio`, `/portfolio/VOO`
- Capture tool: `npm run cwv:measure` (`frontend/scripts/measure-cwv.mjs`)
- Metric thresholds:
  - `LCP <= 2500ms`
  - `INP <= 200ms`
  - `CLS <= 0.1`
- Runs per route: `5` (p75 reporting)

## Evidence Artifacts

- Baseline capture (pre-optimization): `docs/evidence/frontend/cwv-report-2026-03-24T17-11-03.746Z.json`
- Post-fix capture (final): `docs/evidence/frontend/cwv-report-2026-03-24T17-12-49.067Z.json`

## Baseline Results (Pre-Optimization)

| Route | LCP p75 | INP p75 | CLS p75 | Verdict |
| --- | ---: | ---: | ---: | --- |
| `/portfolio` | `320ms` | `232ms` | `0` | `FAIL` (`INP`) |
| `/portfolio/VOO` | `300ms` | `152ms` | `0` | `PASS` |

## Optimization Applied

- Removed panel backdrop blur compositing from `.panel` in `frontend/src/app/styles.css` to reduce interaction/rendering overhead during theme-driven full-page repaint.

## Final Results (Post-Fix)

| Route | LCP p75 | INP p75 | CLS p75 | Verdict |
| --- | ---: | ---: | ---: | --- |
| `/portfolio` | `296ms` | `96ms` | `0` | `PASS` |
| `/portfolio/VOO` | `284ms` | `88ms` | `0` | `PASS` |

## Assessment

- Post-fix CWV lab evidence passes the documented thresholds for both measured routes.
- LCP and CLS remained comfortably under limits in both runs.
- INP regression observed in baseline was resolved after the targeted rendering-cost adjustment.

## Latest Reproducibility Check

- Capture: `docs/evidence/frontend/cwv-report-2026-03-24T18-13-57.449Z.json`
- `/portfolio`: `LCP 292ms`, `INP 80ms`, `CLS 0` (`PASS`)
- `/portfolio/VOO`: `LCP 280ms`, `INP 80ms`, `CLS 0` (`PASS`)
