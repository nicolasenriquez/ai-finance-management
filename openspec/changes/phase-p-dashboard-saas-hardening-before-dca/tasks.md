## 1. Discovery and Fail-First Contracts

- [x] 1.1 Build a compact-route fetch inventory (`Home`, `Analytics`, `Risk`, `Signals`) that classifies each first-surface module as `contract-backed`, `derived`, or `pseudo/static`.
  Notes: Inventory artifact should map each module to current hook/query ownership and expected target owner after route-level orchestration.
  Implementation: Added compact-route inventory with module classifications and target orchestration owners. Artifact: `docs/product/phase-p-compact-route-fetch-inventory.md`.

- [x] 1.2 Add fail-first frontend contract tests for anti-waterfall behavior on first-surface route modules.
  Notes: At minimum validate that independent first-surface dependencies are dispatched concurrently rather than serially.
  Implementation: Added fail-first orchestration contract test that currently fails on missing risk query-hook and query-ownership markers. Artifact: `frontend/src/app/route-performance-orchestration.contract.fail-first.test.ts`.

- [x] 1.3 Add fail-first tests that preserve `Opportunities` label mapping to `/portfolio/signals` and secondary tactical posture.
  Implementation: Added explicit contract assertions for label/slug mapping and secondary tactical posture copy. Artifact: `frontend/src/app/route-performance-orchestration.contract.fail-first.test.ts`.

- [x] 1.4 Capture baseline route evidence for loading latency and first-surface readiness on `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, and `/portfolio/signals`.
  Notes: Evidence should be reproducible and referenced later in validation/docs tasks.
  Implementation: Captured route contract timing baseline plus fail-first evidence command outputs. Artifact: `docs/product/phase-p-dashboard-baseline-evidence.md`.

## 2. Route-Level Performance Orchestration

- [x] 2.1 Refactor first-surface server-state loading to route-level TanStack Query orchestration for Home.

- [x] 2.2 Refactor first-surface server-state loading to route-level TanStack Query orchestration for Analytics and Risk.

- [x] 2.3 Refactor first-surface server-state loading to route-level TanStack Query orchestration for Signals (`Opportunities`).

- [x] 2.4 Introduce lazy loading and bounded suspense boundaries for route bundles and heavy secondary modules without hiding first-surface trust context.

- [x] 2.5 Add intent-aware next-route prefetch hooks for compact-shell navigation to reduce transition latency.

## 3. Chart Realization on Primary Routes

- [x] 3.1 Replace Home pseudo-chart surface with contract-backed portfolio-versus-benchmark Recharts module.

- [x] 3.2 Replace Analytics pseudo-chart surfaces with contract-backed relative-performance, contribution-ranking, and attribution-waterfall modules.

- [x] 3.3 Replace Risk pseudo-chart surfaces with contract-backed drawdown, rolling-risk, and return-distribution modules.

- [x] 3.4 Enforce stable responsive chart container contracts and unit-safe axis/tooltip behavior across primary routes.
  Notes: Use stable parent sizing and explicit guardrails for mixed-unit payloads.

## 4. Opportunities Workspace Hardening

- [x] 4.1 Replace static tactical ranking/watchlist constants with deterministic contract-backed opportunities derivation.

- [x] 4.2 Add reason-code and action-state framing to opportunities candidates, including source freshness and confidence cues where available.

- [x] 4.3 Normalize opportunities async-state copy to factual `loading`, `empty`, `unavailable`, and `error` messages with retry affordances.

- [x] 4.4 Add route continuity checks for opportunities-to-asset-detail drilldown and shell-level tactical framing.

## 5. Visual Density and Shell Signal Prioritization

- [x] 5.1 Reduce non-critical shell chrome density in first viewport while preserving required trust context.

- [x] 5.2 Enforce one dominant first-surface analytical module per primary route and demote secondary evidence below fold or within bounded disclosure.

- [x] 5.3 Add regression tests for module hierarchy and first-viewport readability on `320`, `768`, `1024`, and `1440` widths.

## 6. Documentation and Validation

- [x] 6.1 Run frontend validation gates (`test`, `lint`, `build`) and record route-level performance evidence before/after orchestration and chart realization.

- [x] 6.2 Run OpenSpec validation for the new change and full specs baseline.
  Notes: Record command outputs and any non-blocking environment noise separately from pass/fail results.

- [x] 6.3 Update `docs/product` handoff notes and `CHANGELOG.md` with implemented scope, evidence links, and explicit statement that DCA implementation remains next.
