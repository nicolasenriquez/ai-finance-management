## Why

The compact dashboard reset landed correctly, but first-surface analytical density and perceived performance are still below the target SaaS quality bar. Before starting DCA workflow implementation, the frontend needs one hardening pass that converts placeholder-like modules into contract-backed chart surfaces and removes route-level loading friction.

## What Changes

- Keep the current compact five-route shell as the primary IA (`/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, `/portfolio/asset-detail/:ticker`).
- Preserve `Opportunities` as the visible tactical label while keeping the canonical route slug `/portfolio/signals`.
- Introduce route-level data orchestration for first-viewport modules, with explicit parallel loading behavior and deterministic retry/failure isolation.
- Add lazy loading and bounded `Suspense` boundaries for heavy route modules to reduce first-paint and navigation latency.
- Replace pseudo-chart modules on `Home`, `Analytics`, and `Risk` with contract-backed Recharts visual surfaces.
- Harden async-state behavior by replacing generic `Unavailable` copy with module-factual loading/empty/unavailable/error messaging.
- Reduce shell chrome density so the first viewport prioritizes analytical signal over framing metadata.
- Capture repeatable frontend evidence (tests, build, route performance notes, OpenSpec validation) as implementation closeout before DCA work begins.

## Capabilities

### New Capabilities
- `frontend-compact-dashboard-performance-orchestration`: Route-level server-state orchestration, anti-waterfall behavior, lazy-loading boundaries, and prefetch discipline for compact routes.
- `frontend-compact-dashboard-chart-realization`: Contract-backed chart modules for Home, Analytics, and Risk with stable rendering and explicit unit semantics.
- `frontend-compact-dashboard-opportunities-workspace`: Production-grade opportunities workflow on `/portfolio/signals` with deterministic ranking context, reason-code cues, and explicit tactical-state handling.

### Modified Capabilities
- `frontend-release-readiness`: Extend release-readiness requirements to include compact-route performance evidence, factual async copy quality, and chart-container stability checks for the rebuilt shell.

## Impact

- OpenSpec artifacts under `openspec/changes/phase-p-dashboard-saas-hardening-before-dca/`.
- Frontend route and shell implementation in `frontend/src/app/`, `frontend/src/components/`, `frontend/src/pages/`, and `frontend/src/core/api/`.
- Product/runtime documentation and closeout evidence in `docs/product/`, `docs/guides/`, and `CHANGELOG.md`.
- No backend contract expansion for DCA in this change; DCA workflow changes remain sequenced after this hardening slice.
