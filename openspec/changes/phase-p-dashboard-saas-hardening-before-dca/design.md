## Context

The repository already completed the compact-dashboard reset (`archive-v0-and-build-compact-trading-dashboard`) and established a five-route shell with explicit tactical separation. The remaining gap is quality hardening: primary routes still include pseudo-chart behavior, route-state loading patterns are partially fragmented, and first-surface perceived performance can degrade under serial-fetch patterns.

This change is intentionally sequenced before DCA workflow delivery so tactical and copilot DCA work starts from a stable, faster, and more trustworthy dashboard baseline.

Constraints:
- Preserve the current compact IA and route slugs.
- Preserve passive-investor posture with tactical overlay as secondary.
- Avoid backend contract invention in this slice.
- Keep fail-fast and explicit state behavior.

## Goals / Non-Goals

**Goals:**
- Harden compact-route data loading with route-level orchestration and anti-waterfall behavior.
- Replace pseudo-chart first-surface modules with contract-backed Recharts modules on Home, Analytics, and Risk.
- Upgrade Opportunities (`/portfolio/signals`) to deterministic, contract-backed tactical review.
- Enforce factual async state copy and module-local failure isolation.
- Produce implementation evidence that supports release-readiness and handoff into DCA phases.

**Non-Goals:**
- Expanding IA back to route-heavy workspace patterns (`reports`, `transactions`, `copilot`) as primary navigation.
- Introducing execution-terminal or order-routing UX.
- Implementing DCA policy or copilot DCA-assessment behavior in this change.
- Reworking backend portfolio APIs beyond frontend-consumption alignment.

## Decisions

### Decision: Use route-level TanStack Query orchestration for first-surface data
Adopt route-level query composition for primary modules and remove ad hoc `useEffect`/`useState` fetch orchestration where it drives first-viewport behavior.

Why:
- Centralized orchestration simplifies retry, cache, and loading semantics.
- Reduces waterfall risk by dispatching independent requests in parallel.
- Improves consistency across Home/Analytics/Risk/Signals.

Alternatives considered:
- Keep current custom resource hooks and patch individually. Rejected due to recurring drift and duplicated state semantics.
- Introduce global client store for remote data. Rejected as unnecessary complexity for current route scope.

### Decision: Introduce lazy loading only where it reduces first-surface cost
Apply `React.lazy` + bounded `Suspense` for route bundles and heavy secondary modules while keeping first-surface interpretability visible.

Why:
- Reduces initial route cost without hiding critical trust context.
- Keeps compact-shell navigation responsive during module-heavy route transitions.

Alternatives considered:
- Full eager-loading for all routes. Rejected due to avoidable bundle and transition cost.
- Aggressive micro-splitting at component granularity everywhere. Rejected due to maintenance overhead and unstable UX boundaries.

### Decision: Promote contract-backed charts as first-surface modules on Home/Analytics/Risk
Replace pseudo-chart presentations with real Recharts modules backed by typed contracts and stable container geometry.

Why:
- Aligns UI interpretation with backend truth.
- Increases analytical credibility in first viewport.
- Reduces perception of prototype scaffolding.

Alternatives considered:
- Keep table/list-first primary surfaces and defer charts. Rejected because it weakens explainability and executive scanability.
- Introduce another chart library. Rejected because repo contracts already standardize on Recharts.

### Decision: Keep `Opportunities` visible label on `/portfolio/signals` and upgrade module realism
Retain current route slug + visible label mapping while replacing static tactical lists with deterministic, contract-backed ranking/watchlist logic.

Why:
- Preserves stable routing and existing tests.
- Keeps tactical posture explicit without promoting terminal behavior.
- Directly addresses user-priority opportunities workflow.

Alternatives considered:
- Rename route slug to `/portfolio/opportunities`. Rejected to avoid migration churn and broken assumptions.
- Move opportunities into Home. Rejected because it dilutes route separation and increases clutter.

### Decision: Centralize factual async-state copy contracts
Use one route-module state vocabulary and factual reasoned copy contract for loading/empty/unavailable/error states, with retry affordances for recoverable failures.

Why:
- Eliminates ambiguous generic unavailable text.
- Improves trust and diagnosability.
- Supports consistent accessibility and QA evidence.

Alternatives considered:
- Route-specific custom copy patterns. Rejected due to inconsistency and test burden.

## Risks / Trade-offs

- [Risk] Query-orchestration refactor introduces regressions in route state timing. -> Mitigation: fail-first route contract tests and incremental route-by-route migration.
- [Risk] Recharts module replacement increases implementation complexity in one slice. -> Mitigation: prioritize first-surface charts only; defer secondary cosmetic chart variants.
- [Risk] Lazy-loading boundaries may create temporary perceived flicker. -> Mitigation: stable skeleton geometry and explicit bounded fallbacks.
- [Risk] Opportunities realism depends on availability of current contracts. -> Mitigation: deterministic unavailable states with reason-code and fallback guidance.
- [Risk] Scope creep into DCA implementation delays this hardening. -> Mitigation: explicit non-goal and task guard that excludes DCA policy behavior.

## Migration Plan

1. Establish baseline evidence for current route fetch behavior and first-surface latency.
2. Introduce route-level query orchestration primitives and migrate Home first.
3. Migrate Analytics, Risk, and Signals orchestration with contract tests.
4. Replace first-surface pseudo-chart modules with contract-backed Recharts modules.
5. Harden Opportunities modules and factual async copy contracts.
6. Run validation gates, capture evidence, and update docs/changelog for handoff.

Rollback strategy:
- Keep changes route-scoped and behind typed module boundaries so individual route regressions can be reverted without reverting the entire shell.
- Preserve existing API contracts and avoid backend schema migrations in this slice.

## Open Questions

None.
