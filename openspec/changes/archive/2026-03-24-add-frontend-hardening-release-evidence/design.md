## Context

The repository now includes a React + Vite frontend MVP with summary and lot-detail routes, typed API boundaries, and design tokens with light/dark themes. Product and delivery docs already define quality gates for frontend release readiness, but those gates are still mostly checklist intent rather than completed evidence.

Current constraints:

- Keep analytics scope ledger-only (`open_*`, `realized_*`, `dividend_*`) with no market-value inference.
- Keep implementation inside frontend hardening boundaries; do not start new backend capabilities.
- Preserve deterministic API-to-UI error mapping and fail-fast semantics.
- Treat accessibility and performance evidence as release criteria, not optional follow-up.

Investigation findings informing this hardening pass:

- The accessibility patches in the current diff move the UI in the right direction, but the route shell still spends significant above-the-fold space on editorial hero copy and duplicated explainer cards.
- For a finance workspace, that visual hierarchy reads less like a professional operational surface and more like a landing page, which weakens the intended minimalist/trust-first posture documented elsewhere.
- The current stylesheet imports Google Fonts through a runtime `@import`, which conflicts with the design-system guidance to prefer self-hosted/preloaded fonts and introduces avoidable Core Web Vitals and dependency risk.

## Goals / Non-Goals

**Goals:**

- Prove state reliability for summary and lot-detail UX under success, empty, and error paths.
- Validate accessibility baseline (WCAG 2.2 AA-oriented checks) across both light and dark themes.
- Measure and document CWV outcomes for the MVP views.
- Tighten route-level visual hierarchy so summary and lot-detail pages feel task-first, professional, and minimal rather than editorial.
- Record reproducible evidence and checklist completion in repository docs.

**Non-Goals:**

- Adding new analytics metrics, charting, or market-value views.
- Replatforming frontend stack (no Next.js migration).
- Introducing auth, personalization engines, or new product workflows.

## Decisions

### 1. Treat hardening as evidence work, not feature expansion

Frontend work in this phase will prioritize measurable quality gates. New UI features are out of scope unless required to resolve an accessibility or performance defect.

Alternative considered:

- Continue adding UX features before capturing evidence.
- Rejected because it increases scope while leaving release-readiness unproven.

### 2. Use targeted verification at route and state boundaries

Testing will focus on deterministic, high-risk user flows: summary load, lot-detail load, unknown symbol handling, and failure/retry states.

Alternative considered:

- Broad visual-only review.
- Rejected because it does not lock behavior and is not reproducible.

### 3. Preserve token-driven theming and validate both themes explicitly

Any accessibility checks must pass in light and dark themes, since both are now shipped.

Alternative considered:

- Validate only default theme.
- Rejected because it allows regressions in user-selectable mode.

### 4. Record evidence in docs at the same time as code changes

Checklist and changelog evidence will be updated as validations are completed, keeping docs in sync with actual outcomes.

Alternative considered:

- Defer evidence documentation until after implementation.
- Rejected because it risks drift between real validation state and repo guidance.

### 5. Prefer compact workspace framing over marketing-style hero treatments

For MVP analytics routes, the first viewport should emphasize operational trust signals and immediate task context: page title, ledger timestamp, scope note, and next action. Supporting explanation should stay concise and should not consume the same visual weight as the analytics content itself.

This means the hardening pass may simplify or compact the current hero treatment rather than further decorating it.

Alternative considered:

- Keep the large hero layout and iterate only on copy.
- Rejected because the issue is information hierarchy, not just wording; a polished finance interface should get users to trustworthy data faster.

### 6. Treat font delivery as part of frontend hardening, not a visual afterthought

Primary typography is part of the shipped experience and part of LCP/CWV behavior. Release-ready frontend builds should avoid runtime third-party stylesheet dependencies for core fonts and instead use bundled/self-hosted assets or a documented fallback strategy with validated metrics.

Alternative considered:

- Leave the current runtime font import in place and optimize elsewhere.
- Rejected because it keeps a preventable network dependency in the critical path and weakens the credibility of final performance evidence.

## Risks / Trade-offs

- [Risk] Accessibility findings may require CSS/component rework late in the phase. -> Mitigation: run audits early and patch iteratively.
- [Risk] Performance targets may conflict with visual polish decisions. -> Mitigation: prioritize CWV budgets over decorative effects.
- [Risk] Environment limits can block certain audits in this sandbox. -> Mitigation: separate local/sandbox evidence from full environment evidence and document gaps explicitly.
- [Risk] Existing backend validation drift can obscure frontend-specific readiness. -> Mitigation: keep frontend validation scope explicit and report unrelated baseline failures separately.
- [Risk] Simplifying the hero/header may remove explanatory copy users currently rely on. -> Mitigation: preserve one concise sentence of scope context and keep deeper explanations in supporting cards/notes only where they materially help task completion.

## Migration Plan

1. Add/expand frontend tests for critical state and navigation behavior.
2. Audit route-level hierarchy and simplify any hero/header patterns that delay access to trust-critical analytics context.
3. Run accessibility audits and fix identified issues.
4. Measure CWV and apply targeted optimizations where needed, including font-delivery hardening if required.
5. Update docs/checklist/changelog with concrete evidence artifacts.
6. Run final frontend validation and report PASS/PARTIAL PASS with blockers.

Rollback strategy:

- Revert frontend hardening patches and docs updates as one change if regressions are introduced.
- No backend migrations or data rollbacks are required.

## Open Questions

None blocking for implementation. Environment-specific evidence capture paths may vary based on available local tooling.
