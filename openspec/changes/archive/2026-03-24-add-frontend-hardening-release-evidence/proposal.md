## Why

The frontend MVP foundation is now implemented and documented, but Phase 5 remains incomplete because accessibility, performance, and release-evidence gates are not yet proven end-to-end. This change closes that gap so frontend readiness is based on evidence rather than visual inspection.

## What Changes

- Add explicit frontend hardening requirements for keyboard/focus behavior, contrast, and reduced-motion handling across summary and lot-detail screens.
- Add verification coverage for critical frontend states and route flows (`success`, `empty`, `404`, `4xx/5xx`).
- Add release evidence requirements for Core Web Vitals and accessibility artifacts referenced by the frontend delivery checklist.
- Clarify professional/minimalist route-level hierarchy requirements so shipped pages foreground ledger timestamp, scope posture, and primary navigation before decorative supporting copy.
- Clarify frontend asset-delivery expectations for release readiness, including production-safe typography delivery instead of runtime third-party stylesheet dependencies for core fonts.
- Add implementation tasks to measure, fix, and document frontend hardening outcomes without expanding unsupported market-value scope.

## Capabilities

### New Capabilities
- `frontend-release-readiness`: Evidence-driven frontend hardening for accessibility, performance, and deterministic state behavior in the current React MVP.

### Modified Capabilities
- `portfolio-analytics`: Clarify frontend-consumption guardrails for error-state mapping and no-inference behavior when API responses are empty, invalid, or unavailable.

## Impact

- Affected code: frontend tests and page/feature components for state handling, accessibility semantics, and performance adjustments.
- Affected docs: frontend checklist, design-system guidance, frontend standard, validation guidance, and changelog evidence entries.
- Validation scope: frontend test/build plus targeted accessibility and performance evidence capture.
- Systems: no backend schema or API contract expansion; this change hardens frontend consumption of the existing ledger-only analytics contract.
