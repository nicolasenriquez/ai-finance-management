# Frontend Standard

## Purpose

This standard defines non-negotiable quality gates for frontend delivery in this repository.

## Scope

Applies to:

- portfolio summary UI
- lot-detail UI
- shared frontend components, formatting utilities, and state handling

## Core Principles

- Preserve ledger-first truth.
- Fail explicitly; never hide unsupported states.
- Keep behavior deterministic.
- Treat accessibility and performance as release gates.

## Contract Integrity Rules

- Frontend must consume backend response contracts as-is.
- Frontend must not infer unsupported market or FX values.
- Unknown-symbol responses must render explicit not-found behavior.
- `as_of_ledger_at` must be visible on analytics screens.

## Accessibility Rules (WCAG 2.2 AA Baseline)

- Text contrast must satisfy AA contrast requirements.
- If multiple themes are shipped, each theme must independently satisfy contrast requirements.
- Keyboard focus must always be visible.
- Focus indicators must be clear and non-ambiguous.
- Interactive controls must meet minimum target-size expectations.
- Motion must respect reduced-motion system preferences.
- Semantic HTML and ARIA labels must provide accessible names.

Required WCAG mapping for MVP screens:

| Success Criterion | Requirement | Verification Method |
| --- | --- | --- |
| `1.4.3 Contrast (Minimum)` | Text contrast meets AA thresholds (normal and large text) | Automated contrast audit + manual spot checks |
| `2.4.7 Focus Visible` | Keyboard focus is visible on all interactive controls | Manual keyboard walkthrough |
| `2.4.13 Focus Appearance (Minimum)` | Focus indicator has clear area/contrast and is not ambiguous | Manual visual verification against design tokens |
| `2.5.8 Target Size (Minimum)` | Interactive targets meet minimum size or spacing exceptions | Manual measurement in browser dev tools |
| `3.3.1 Error Identification` | Error states identify what failed and where relevant | API error-state UX review |

## Performance Rules

Core Web Vitals target profile:

- LCP: <= 2.5s at p75
- INP: <= 200ms at p75
- CLS: <= 0.1 at p75

Additional rules:

- Avoid layout shift from async content and image loading.
- Keep first-load UI usable before secondary enhancement modules.
- Avoid heavy animation and long-running main-thread work.
- Primary typography in release builds must not depend on runtime third-party stylesheet imports; use bundled/self-hosted assets or a validated fallback strategy.
- Capture field or lab evidence for LCP, INP, and CLS before release.

## UX Reliability Rules

- Loading states must exist for every async view.
- Empty states must explain whether there is no data or unsupported scope.
- Error states must include factual reason and retry action.
- Financial labels must remain consistent across screens.
- Theme changes must not alter the semantic meaning of status colors or labels.
- Route-level composition must prioritize task-critical context; title, ledger timestamp, scope note, and next action should appear before decorative supporting copy on standard laptop widths.
- Core analytics routes must avoid marketing-style hero treatments that delay access to trustworthy data.

## Data Formatting Rules

- Quantities: preserve high precision expected by backend.
- Money: always render with stable two-decimal currency formatting.
- Symbols: render canonical uppercase from API output.
- Timestamps: show user-friendly local format with precise context.
- Financial calculations must use decimal-safe utilities, not binary float arithmetic.
- If client-side rounding is needed, rounding mode must be explicit and documented.
- Any client-side derived overview metric must identify that it is derived from API rows rather than persisted as a backend-native KPI.

## Testing And Verification Rules

- Add unit tests for critical formatting and state mapping utilities.
- Add integration or E2E coverage for:
  - summary fetch success
  - lot detail success
  - unknown symbol flow
  - API error rendering
- Add coverage for theme preference resolution if a user-selectable theme ships.
- Include accessibility test pass evidence for core screens.
- Include performance measurement evidence for core screens.
- Include evidence artifacts in the implementation PR/changeset:
  - keyboard navigation walkthrough notes
  - accessibility scan output
  - Core Web Vitals report snapshot

## Documentation Rules

- Any frontend behavior change must update relevant frontend docs.
- New KPI or metric presentation must include data-source provenance notes.
- Any deferred behavior must be documented explicitly, not implied.
