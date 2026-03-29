# Frontend Keyboard Walkthrough - 2026-03-28

## Scope

- Routes: `/portfolio`, `/portfolio/VOO`, `/portfolio/UNKNOWN`, `/portfolio/ERR500`
- Workspace routes: `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/transactions`
- Viewport: desktop `1440x900`
- Source: automated tab-sequence and keyboard activation checks via Playwright

## Results

- First interactive summary row found by keyboard tabbing: `FAIL`
- Enter on focused summary row navigates to lot detail: `FAIL`
- Lot-detail back link is keyboard-reachable: `FAIL`
- Keyboard activation on back link returns to summary: `FAIL`
- 404 screen retry button is keyboard-reachable: `PASS`
- 404 screen back link is keyboard-reachable: `PASS`
- 500 screen retry button is keyboard-reachable: `PASS`
- 500 screen back link is keyboard-reachable: `PASS`
- Workspace analytics tab is keyboard-reachable: `PASS`
- Enter on analytics tab navigates to analytics route: `PASS`
- Workspace risk tab is keyboard-reachable: `PASS`
- Enter on risk tab navigates to risk route: `PASS`
- Workspace transactions tab is keyboard-reachable: `PASS`
- Enter on transactions tab navigates to transactions route: `PASS`

## Summary Tab Sequence (first 8 focus stops)

1. a.brand-mark | role=n/a | label=Open portfolio summary
2. button.theme-toggle | role=n/a | label=Switch to dark theme
3. select.period-control__select | role=n/a | label=Select analytics period
4. a.button-secondary | role=n/a | label=Open grouped summary
5. a.workspace-nav__link.workspace-nav__link--active | role=n/a | label=Home
6. a.workspace-nav__link | role=n/a | label=Analytics
7. a.workspace-nav__link | role=n/a | label=Risk
8. a.workspace-nav__link | role=n/a | label=Transactions

## Raw Evidence

- JSON report: `docs/evidence/frontend/keyboard-walkthrough-2026-03-28.json`
