## Context

The current portfolio workspace already covers `Home`, `Analytics`, `Risk`, `Transactions`, `Quant/Reports`, and `Copilot`, but it grew feature-by-feature and now carries too much route fragmentation, card-heavy composition, and inconsistent scanning rhythm for the next stage of ML-driven insight. `phase-i` will increase analytical depth through signals, CAPM, and forecasting; this change prepares the frontend so those contracts land in a workspace that is easier to navigate, denser without becoming noisy, and clearer about trust and freshness.

This design also responds to two external inspiration sources:

- `OpenStock` as product-pattern inspiration for fast navigation, watchlist/search behaviors, and analytical dashboard composition.
- `impeccable` plus the provided frontend design guidance as process inspiration for visual restraint, stronger hierarchy, and more deliberate motion.

Constraints:

- Keep the existing React/Vite/TypeScript frontend architecture.
- Preserve the current backend contract posture; this phase is primarily frontend and information-architecture work.
- Keep `Recharts` as the v1 chart foundation unless a separate evidence-backed decision changes that.
- Avoid direct code reuse from AGPL repositories; inspiration is limited to patterns and heuristics.
- Treat `.codex/skills/emil-design-eng/SKILL.md` as a required implementation rubric for UI polish, animation/easing choices, and component interaction quality.

## Goals / Non-Goals

**Goals:**

- Introduce a persistent portfolio workspace shell that reduces route fragmentation and makes high-value destinations discoverable in one interaction.
- Provide one global command palette for route jump, symbol search, and analytical action launch.
- Recompose major routes around a `Core 10` first-pass interpretation layer, with advanced diagnostics secondary.
- Improve personal-finance usefulness by elevating allocation drift, dividend income, goal progress, forecast confidence, and trust/freshness signals.
- Make copilot access persistent within the workspace while preserving explicit evidence, limitations, and read-only guardrails.
- Provide a desktop copilot panel that docks on the right and can collapse/expand without losing conversation continuity.
- Provide recommendation chips for follow-up prompts and composer support for attachment references to previously ingested documents.
- Ship a visually stronger but restrained analytical UI: denser layout, calmer chrome, clearer type hierarchy, and a small number of meaningful motions.
- Keep mobile and desktop behavior intentional rather than scaling the desktop grid down mechanically.

**Non-Goals:**

- Replacing backend analytics contracts or introducing new portfolio math in this change.
- Switching away from `Recharts`.
- Building a marketing-style hero experience inside the product workspace.
- Copying code or component structure directly from OpenStock or impeccable.
- Adding execution, order routing, or hidden automation affordances to the copilot or workspace shell.
- Supporting raw-file multipart uploads directly in copilot chat interactions.
- Enabling free-form SQL authoring from frontend chat controls.

## Decisions

### Decision: Keep `phase-j` separate from `phase-i`

This UX/UI change remains a dedicated follow-up to the ML/time-series change rather than being merged into `phase-i`.

Rationale:

- `phase-i` already carries backend contract and governance risk.
- UX shell and route composition work will otherwise hide backend delivery risk and slow both tracks.
- A separate change keeps the frontend redesign implementable in slices even if some ML endpoints arrive later.

Alternatives considered:

- Merge all UX work into `phase-i`: rejected because it creates one oversized change with mixed acceptance criteria.

### Decision: Introduce a persistent workspace shell with command palette

The workspace will move from page-to-page navigation toward one shell with stable navigation, shared context, and quick-jump search.

Rationale:

- Analytical work benefits from short travel distance between routes, symbols, and reports.
- A command palette is higher leverage than adding more visible buttons or route-local search boxes.
- Shared shell context reduces repeated control clusters across pages.

Alternatives considered:

- Keep route-local controls only: rejected because it preserves fragmentation.
- Add more top-nav tabs without search: rejected because it does not scale to symbol lookup or future saved views.

### Decision: Apply a restrained analytical visual system instead of dashboard-card accumulation

The visual direction will favor layout, spacing, type contrast, and selective emphasis over repeated cards and decorative chrome.

Visual thesis:

- A calm analytical cockpit with dark neutral structure, one controlled accent, sharper typography, and strong scan hierarchy for portfolio decision support.

Content plan:

- Shell and context strip
- Route-specific primary analytical surface
- Secondary evidence or drill-down surface
- Copilot/evidence access as assistant context, not the main visual anchor

Interaction thesis:

- Fast command-palette summon and jump
- Route-enter and panel-expand motion that clarifies hierarchy
- Sticky context strip or inspector transitions that preserve orientation during scrolling

Rationale:

- The workspace is an operational product surface, not a homepage.
- Utility copy and strong hierarchy improve speed of interpretation more than decorative density.
- The provided frontend guidance explicitly rejects generic SaaS card mosaics, which matches the current improvement target.

Alternatives considered:

- Heavy gradient/card treatment: rejected because it competes with the data itself.
- Minimal change with only token cleanup: rejected because it would not materially improve discoverability or scan speed.

### Decision: Preserve dedicated copilot depth while adding responsive docked versus expanded behavior

Copilot stays within the workspace contract but gains a persistent launcher, contextual handoff from surrounding analytical routes, a collapsible docked-right presentation on desktop, and a full-screen presentation on mobile.

Rationale:

- Users need fast access to the copilot without abandoning the analytical surface they were inspecting.
- A persistent launcher answers the discoverability gap while keeping the full evidence experience available.
- Context handoff lets the copilot start from current scope, symbol, and period rather than a blank interaction.
- Desktop has enough width for a lateral assistant surface without displacing the primary analytical route entirely.
- Collapse/expand controls let users recover analytical viewport space without abandoning copilot state.
- Mobile needs a full-screen copilot route or overlay to preserve readability, keyboard safety, and evidence visibility.

Alternatives considered:

- Full-page-only copilot: rejected because it breaks analytical continuity.
- Docked-only copilot with no expanded mode: rejected because evidence-heavy answers need room.
- Same presentation mode on every breakpoint: rejected because it degrades either desktop continuity or mobile readability.

### Decision: Suggestion chips and attachment references are frontend surfaces over backend-governed contracts

Copilot suggestion bubbles and attachment chips will be rendered as frontend affordances that consume typed backend metadata (`prompt_suggestions`, `document_id` references).

Rationale:

- Recommendation chips improve discoverability of high-value analytical follow-ups.
- Attachment references should be explicit and removable in the composer before submit.
- Reusing backend-governed references avoids introducing multipart upload complexity into copilot chat routes.

Alternatives considered:

- Generate suggestion chips purely in frontend without backend context: rejected due to weaker state awareness and higher drift risk.
- Add binary upload directly in copilot composer: rejected because ingestion should remain a separate trusted flow.

### Decision: Use KPI governance as the enforcement point for “Core 10” and personal-finance relevance

The KPI catalog will drive what gets promoted, where it appears, and what interpretation copy it requires.

Rationale:

- Without governance, redesign work quickly regresses into route-by-route preference changes.
- Personal-finance users need portfolio-operating metrics, not only generic market metrics.
- This change needs a durable prioritization model, not just visual adjustments.

Alternatives considered:

- Handle KPI promotion informally in page components: rejected because it is not auditable or stable across iterations.

### Decision: Keep this phase frontend-first and dependency-light

Implementation should prefer existing frontend primitives and small headless utilities over a large UI-framework swap.

Rationale:

- The value comes from composition and interaction design, not from introducing a new component stack.
- Large dependency additions would slow rollout and complicate design consistency.

Alternatives considered:

- Adopt a full dashboard framework: rejected because it would increase migration cost and visual inconsistency risk.

## Risks / Trade-offs

- [Scope creep from “redesign everything” pressure] -> Keep the change bounded to workspace shell, route composition, KPI prioritization, and copilot access patterns; defer new backend metrics to follow-up changes.
- [License contamination from inspiration repos] -> Use public repos only as reference inputs for product patterns and visual heuristics; do not port code or styling tokens verbatim.
- [Denser layouts harming accessibility] -> Enforce keyboard reachability, contrast, tabular numeric rhythm, and responsive collapse rules as acceptance criteria.
- [Persistent shell and panel behavior increasing frontend state complexity] -> Centralize workspace context and copilot UI state in shared route-safe primitives instead of page-local state.
- [Visual polish causing performance regressions] -> Use restrained animation, code-split palette/panel behavior where needed, and validate build size/CWV before rollout.
- [Collapsible panel interactions can reduce accessibility if focus behavior is inconsistent] -> Define keyboard focus restoration and aria-expanded semantics as acceptance criteria.
- [Suggestion chips can bias user prompts toward low-signal questions] -> Gate chips by backend context quality and keep a strict bounded count with deterministic ordering.

## Migration Plan

1. Introduce shared shell, context-strip, and route-layout primitives without changing route contracts.
2. Add command palette and shared navigation model behind the existing workspace routes.
3. Refactor route first viewports and KPI groupings to the `Core 10` model, preserving existing endpoint contracts.
4. Add persistent copilot launcher with desktop docked-collapsible behavior, mobile full-screen behavior, and context handoff.
5. Add copilot suggestion-chip rendering and attachment-reference controls backed by typed backend metadata.
6. Remove superseded one-off layout wrappers once all workspace routes use shared primitives.

Rollback:

- Keep route components independently renderable during migration so the shell can be disabled without removing route pages.
- Land shell and copilot access work in separable slices so regressions can be isolated to one surface.

## Open Questions

- Do we want recent items only in the first command palette release, or also saved views/watchlists?
- Which goal-progress metric can be derived from current contracts, and which part requires a later planning/budget capability?

## Frozen Execution Baseline (2026-04-05)

This section freezes scope for tasks `1.1` through `1.4` so page refactors can proceed without
re-opening information architecture decisions.

### 1) Workspace Audit Snapshot

#### Current route and first-viewport audit

| Route | First viewport now | Observed issue to replace in phase-j |
| --- | --- | --- |
| `/portfolio/home` | Health synthesis plus KPI cards and trend start | Competes between "executive summary" and "analysis launchpad"; period/profile controls are route-local only. |
| `/portfolio/analytics` | Trend chart followed by contribution diagnostics | Two near-primary interpretation blocks in first viewport; no shared "current context" carryover contract. |
| `/portfolio/risk` | Scope + symbol + period controls plus estimator/risk modules | Most control-dense first viewport; route-specific scope reset behavior is not shared with other routes. |
| `/portfolio/reports` | Quant scorecards and report lifecycle controls | First viewport is operationally heavy; report lifecycle actions compete with interpretation context. |
| `/portfolio/copilot` | Full-page composer/state/evidence stack | Copilot is isolated to one route; no persistent launcher from analysis routes. |
| `/portfolio/transactions` | Filters and ledger table | Route lives in same shell but has no consistent context-carryover semantics with analytical routes. |

#### Shared primitive and duplication audit

- `PortfolioWorkspaceLayout` gives stable nav + trust strip, but no command palette or shared context
  state machine.
- `actions` are injected per route, causing repeated control construction (`PortfolioChartPeriodControl`,
  scope selects, symbol inputs, and back links) with route-specific behavior differences.
- Search-param parsing (`period`, `scope`, `instrument_symbol`) is implemented independently in pages.
- State copy for `loading`, `ready`, `unavailable`, `error`, and `retry` is route-authored, not governed
  by one shared trust-state copy registry.
- `Copilot` exists only as a dedicated route; there is no persistent shell-level entry pattern for quick
  launch and context-preserving return.

### 2) Frozen Information Architecture (phase-j)

#### Shell zones (frozen)

1. Masthead zone: brand and theme toggle (keep existing).
2. Navigation + command zone: route list plus global command palette trigger.
3. Context strip zone: active scope/symbol/period/freshness/provenance tokens.
4. Main route canvas: one primary first-viewport analytical job per route.
5. Copilot zone: persistent launcher everywhere; docked panel on desktop and full-screen presentation on mobile.

#### Command palette v1 scope (frozen)

- Route jump: `home`, `analytics`, `risk`, `reports`, `copilot`, `transactions`.
- Symbol lookup: quick jump into symbol-compatible destinations (`risk`, `copilot`, lot detail).
- Approved analytical actions:
  - "Open risk for <symbol>"
  - "Open copilot with current context"
  - "Open reports for current period"
- Out of scope for v1: saved views, watchlists, free-form command execution.

#### Context carryover and reset contract (frozen)

- Shared workspace context keys: `period`, `scope`, `instrument_symbol`, `source_route`.
- Carry forward compatible keys on route transitions.
- Reset rules:
  - if destination does not support instrument scope, set `scope=portfolio` and clear `instrument_symbol`;
  - if destination supports instrument scope but symbol is invalid/empty, clear `instrument_symbol` and show explicit reset copy;
  - do not silently submit stale symbol/scope to unsupported routes.
- Explicit reset copy is required whenever incompatible context is cleared.

#### Copilot launch modes (frozen)

- Desktop (`>= 1024px`): right-docked panel with collapse/expand; conversation state preserved.
- Mobile (`< 1024px`): full-screen copilot presentation.
- Expanded deep-session mode remains available as dedicated copilot route.
- Context handoff payload into copilot launch: `route`, `period`, `scope`, `instrument_symbol` when present.

### 3) Frozen Core 10 KPI Catalog

`Core 10` metrics are the promoted first-pass interpretation layer. Advanced diagnostics remain below.

| Core KPI ID | Route owner | Decision tags | Primary interpretation |
| --- | --- | --- | --- |
| `market_value_usd` | Home | `allocation_review` | Current portfolio scale and exposure. |
| `unrealized_gain_pct` | Home | `allocation_review`, `risk_posture` | Open-position mark-to-market posture. |
| `realized_gain_usd` | Home | `goal_progress` | Locked gains/losses versus plan. |
| `dividend_net_usd` | Home | `income_monitoring` | Net income contribution from dividends. |
| `top_contribution_concentration_pct` | Analytics | `allocation_review`, `risk_posture` | How much of period move is concentrated in one symbol. |
| `max_drawdown_pct` | Risk | `risk_posture` | Peak-to-trough stress magnitude. |
| `volatility_annualized_pct` | Risk | `risk_posture` | Realized dispersion/risk budget pressure. |
| `beta_ratio` | Risk | `risk_posture` | Market sensitivity relative to benchmark context. |
| `goal_hit_probability_pct` | Quant/Reports | `goal_progress` | Probability of reaching selected goal threshold. |
| `forecast_confidence_pct` | Quant/Reports | `forecast_interpretation` | Confidence quality for promoted forecast outputs. |

#### Additional governance freeze

- Every promoted KPI must include: tier (`core_10` or `advanced`), owning route, decision tags,
  and one plain-language interpretation sentence.
- Freshness/provenance tokens are mandatory route context, but not counted as Core 10 KPIs.

### 4) Emil Design Rubric Scope (frozen for shell/navigation/copilot)

The `emil-design-eng` skill is mandatory for this phase. The following principles are in scope:

- High-frequency interaction rule:
  - keyboard-open command palette should avoid open/close animation.
- Purpose-first motion only:
  - animation must communicate hierarchy/state, not decorative movement.
- Easing discipline:
  - entering UI surfaces use strong `ease-out`; avoid `ease-in` in UI transitions.
- Duration bounds:
  - interaction transitions target `100-250ms`; common UI transitions stay `<300ms`.
- Press feedback:
  - interactive buttons/controls provide explicit active-state response.
- Origin-aware surface motion:
  - anchored popovers scale from trigger origin; modals remain centered.
- State consistency:
  - transitions avoid `all`; animate explicit properties only.

## Implementation Rubric

- Implementation and review for this change MUST apply the `emil-design-eng` skill in `.codex/skills/emil-design-eng/SKILL.md`.
- Animation decisions MUST use the skill's decision framework (frequency, purpose, easing, duration) and avoid frequent-use motion overhead.
- UI review artifacts for interaction/motion choices SHOULD use the skill's required Before/After/Why table format for consistency.
