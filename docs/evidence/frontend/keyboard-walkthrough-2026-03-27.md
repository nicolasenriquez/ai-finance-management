# Frontend Keyboard Walkthrough - 2026-03-27

## Scope

- Routes: `/portfolio`, `/portfolio/VOO`, `/portfolio/UNKNOWN`, `/portfolio/ERR500`
- Viewport: desktop `1440x900`
- Source: automated tab-sequence and keyboard activation checks via Playwright

## Results

- First interactive summary row found by keyboard tabbing: `PASS`
- Enter on focused summary row navigates to lot detail: `PASS`
- Lot-detail back link is keyboard-reachable: `PASS`
- Keyboard activation on back link returns to summary: `PASS`
- 404 screen retry button is keyboard-reachable: `PASS`
- 404 screen back link is keyboard-reachable: `PASS`
- 500 screen retry button is keyboard-reachable: `PASS`
- 500 screen back link is keyboard-reachable: `PASS`

## Summary Tab Sequence (first 8 focus stops)

1. a.brand-mark | role=n/a | label=Open portfolio summary
2. button.theme-toggle | role=n/a | label=Switch to dark theme
3. tr.data-table__row.data-table__row--interactive | role=link | label=Open lot detail for VOO

## Raw Evidence

- JSON report: `docs/evidence/frontend/keyboard-walkthrough-2026-03-27.json`
