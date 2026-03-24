# Frontend Delivery Checklist

## Purpose

This checklist turns the frontend documentation pack into an execution gate for implementation and review.

## Phase 1: Contract Lock

- [ ] Frontend scope confirmed against `docs/product/frontend-mvp-prd-addendum.md`
- [ ] API response contracts mapped and reviewed
- [ ] Explicit list of out-of-scope metrics documented in UI copy
- [ ] Unknown-symbol behavior approved (`404` -> not-found state)
- [ ] API error matrix (`404`/`422`/`500`) mapped to concrete UI states
- [ ] API prefix handling is environment-driven (no hardcoded base URL assumptions)

## Phase 2: Design System Foundation

- [ ] Design tokens defined with semantic naming
- [ ] Light and dark theme token parity reviewed
- [ ] Typography and numeric legibility rules implemented
- [ ] Table component supports keyboard navigation and focus ring
- [ ] Loading, empty, and error states designed before feature polish
- [ ] Decimal-safe formatting and calculation utility boundary implemented

## Phase 3: Summary View

- [ ] Summary endpoint integrated: `GET /api/portfolio/summary`
- [ ] `as_of_ledger_at` displayed in header context
- [ ] KPI columns formatted per money/quantity rules
- [ ] Row interaction to lot detail supports mouse and keyboard

## Phase 4: Lot Detail View

- [ ] Lot detail endpoint integrated: `GET /api/portfolio/lots/{instrument_symbol}`
- [ ] Canonical symbol label rendered from API response
- [ ] Disposition history is explainable and readable
- [ ] Not-found and generic error states validated

## Phase 5: Accessibility And Performance

- [ ] WCAG 2.2 AA checks pass for core screens
- [ ] Focus visibility and focus appearance verified
- [ ] Light theme and dark theme both satisfy contrast requirements
- [ ] `prefers-reduced-motion` behavior tested
- [ ] Core Web Vitals targets measured and tracked
- [ ] WCAG criterion mapping evidence captured for MVP screens

## Phase 6: Release Readiness

- [ ] Frontend documentation updated to reflect shipped behavior
- [ ] Acceptance criteria from product addendum validated
- [ ] Known limitations clearly documented
- [ ] Change logged in `CHANGELOG.md` with validation evidence
- [ ] Evidence artifacts linked in PR/changeset

## Evidence Artifacts (Required)

- [ ] Desktop summary screenshot with `as_of_ledger_at` visible
- [ ] Desktop summary screenshot in dark theme
- [ ] Mobile summary screenshot with responsive table behavior
- [ ] Lot-detail screenshot showing disposition history
- [ ] 404 not-found state screenshot for unknown symbol
- [ ] 500 error state screenshot with retry affordance
- [ ] Keyboard walkthrough notes (tab order + focus visibility)
- [ ] Accessibility scan report (axe/Lighthouse or equivalent)
- [ ] Performance report with LCP, INP, and CLS values

## Review Questions Before Merge

- [ ] Does UI imply unsupported valuation or FX math?
- [ ] Are all failures explicit and user-comprehensible?
- [ ] Can a user trace summary -> lot detail without ambiguity?
- [ ] Is the as-of ledger timestamp always visible where needed?
