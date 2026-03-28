# Frontend Delivery Checklist

## Purpose

This checklist turns the frontend documentation pack into an execution gate for implementation and review.

## Phase 1: Contract Lock

- [x] Frontend scope confirmed against `docs/product/frontend-mvp-prd-addendum.md`
- [x] API response contracts mapped and reviewed
- [x] Explicit list of out-of-scope metrics documented in UI copy
- [x] Unknown-symbol behavior approved (`404` -> not-found state)
- [x] API error matrix (`404`/`422`/`500`) mapped to concrete UI states
- [x] API prefix handling is environment-driven (no hardcoded base URL assumptions)

## Phase 2: Design System Foundation

- [x] Design tokens defined with semantic naming
- [x] Light and dark theme token parity reviewed
- [x] Typography and numeric legibility rules implemented
- [x] Route-level header uses compact workspace hierarchy instead of marketing-style hero framing
- [x] Table component supports keyboard navigation and focus ring
- [x] Loading, empty, and error states designed before feature polish
- [x] Decimal-safe formatting and calculation utility boundary implemented
- [x] Production font delivery is bundled/self-hosted or otherwise validated without runtime third-party stylesheet dependency

## Phase 3: Summary View

- [x] Summary endpoint integrated: `GET /api/portfolio/summary`
- [x] `as_of_ledger_at` displayed in header context
- [x] KPI columns formatted per money/quantity rules
- [x] Row interaction to lot detail supports mouse and keyboard

## Phase 4: Lot Detail View

- [x] Lot detail endpoint integrated: `GET /api/portfolio/lots/{instrument_symbol}`
- [x] Canonical symbol label rendered from API response
- [x] Disposition history is explainable and readable
- [x] Not-found and generic error states validated

## Phase 5: Accessibility And Performance

- [x] WCAG 2.2 AA checks pass for core screens
- [x] Focus visibility and focus appearance verified
- [x] Light theme and dark theme both satisfy contrast requirements
- [x] `prefers-reduced-motion` behavior tested
- [x] Core Web Vitals targets measured and tracked
- [x] WCAG criterion mapping evidence captured for MVP screens

## Phase 6: Release Readiness

- [x] Frontend documentation updated to reflect shipped behavior
- [x] Acceptance criteria from product addendum validated
- [x] Known limitations clearly documented
- [x] Change logged in `CHANGELOG.md` with validation evidence
- [x] Evidence artifacts linked in PR/changeset

## Evidence Artifacts (Required)

- [x] Desktop summary screenshot with `as_of_ledger_at` visible (`docs/evidence/frontend/screenshots-2026-03-28/desktop-summary-ledger-timestamp.png`)
- [x] Desktop first-viewport screenshot showing title, timestamp, scope note, and primary action visible together (`docs/evidence/frontend/screenshots-2026-03-28/desktop-summary-first-viewport.png`)
- [x] Desktop summary screenshot in dark theme (`docs/evidence/frontend/screenshots-2026-03-28/desktop-summary-dark-theme.png`)
- [x] Mobile summary screenshot with responsive table behavior (`docs/evidence/frontend/screenshots-2026-03-28/mobile-summary-responsive.png`)
- [x] Lot-detail screenshot showing disposition history (`docs/evidence/frontend/screenshots-2026-03-28/lot-detail-disposition-history.png`)
- [x] 404 not-found state screenshot for unknown symbol (`docs/evidence/frontend/screenshots-2026-03-28/lot-detail-not-found-404.png`)
- [x] 500 error state screenshot with retry affordance (`docs/evidence/frontend/screenshots-2026-03-28/lot-detail-server-error-500.png`)
- [x] Workspace home screenshot (`docs/evidence/frontend/screenshots-2026-03-28/workspace-home.png`)
- [x] Workspace analytics screenshot (`docs/evidence/frontend/screenshots-2026-03-28/workspace-analytics.png`)
- [x] Workspace risk screenshot (`docs/evidence/frontend/screenshots-2026-03-28/workspace-risk.png`)
- [x] Workspace transactions screenshot (`docs/evidence/frontend/screenshots-2026-03-28/workspace-transactions.png`)
- [x] Keyboard walkthrough notes (tab order + focus visibility) (`docs/evidence/frontend/keyboard-walkthrough-2026-03-28.md`)
- [x] Accessibility scan report (axe/Lighthouse or equivalent) (`docs/evidence/frontend/accessibility-scan-2026-03-28.md`)
- [x] Performance report with LCP, INP, and CLS values (`docs/evidence/frontend/cwv-report-2026-03-28.md`)

## Review Questions Before Merge

- [x] Does UI imply unsupported valuation or FX math?
- [x] Are all failures explicit and user-comprehensible?
- [x] Can a user trace summary -> lot detail without ambiguity?
- [x] Is the as-of ledger timestamp always visible where needed?
- [x] Does the first viewport feel like a finance workspace rather than a marketing page?
