# Frontend Accessibility Scan - 2026-03-28

## Method

- Tooling: Playwright Chromium + DOM semantic checks + explicit role inventory.
- Scope: `/portfolio`, `/portfolio/VOO`, `/portfolio/UNKNOWN`, `/portfolio/ERR500`, `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/transactions`.
- Focus: landmark/heading structure, interactive naming, keyboard-row semantics, workspace navigation tabs, and error-banner role mapping.

## Route Results

| Route | Verdict | Findings |
| --- | --- | --- |
| `/portfolio` | `FAIL` | Expected at least one keyboard-focusable summary row. |
| `/portfolio/VOO` | `PASS` | No blocking findings. |
| `/portfolio/UNKNOWN` | `PASS` | No blocking findings. |
| `/portfolio/ERR500` | `PASS` | No blocking findings. |
| `/portfolio/home?period=30D` | `PASS` | No blocking findings. |
| `/portfolio/analytics?period=90D` | `PASS` | No blocking findings. |
| `/portfolio/risk?period=252D` | `PASS` | No blocking findings. |
| `/portfolio/transactions` | `PASS` | No blocking findings. |

## WCAG Mapping Notes

- `1.3.1 Info and Relationships`: verified main landmark and heading structure per route.
- `2.4.7 Focus Visible`: paired with keyboard walkthrough evidence in `docs/evidence/frontend/keyboard-walkthrough-2026-03-28.md`.
- `3.3.1 Error Identification`: verified dedicated `status` (`404`) and `alert` (`500`) banners.
- `4.1.2 Name, Role, Value`: verified button/link naming, interactive summary row semantics, and workspace-tab semantics.

## Raw Evidence

- JSON report: `docs/evidence/frontend/accessibility-scan-2026-03-28.json`
