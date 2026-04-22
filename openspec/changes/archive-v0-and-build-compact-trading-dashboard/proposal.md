## Why

The current frontend contains useful logic, but the dashboard surface has become too populated, too tall, and too hard to read for the value it is delivering. The user wants a reset toward a personal investing cockpit that is:

- compact
- didactic
- opportunity-first
- useful for long-term buy/add decisions
- useful for reviewing current portfolio health

This proposal is grounded in five inputs:

1. the repository state and current proposal history
2. the user's transcript-driven financial framework ("Beast Mode" + "This Changes Everything")
3. online research across Fidelity, Schwab, Morningstar, and Koyfin on long-term-investor metrics, technical timing, watchlists, portfolio review, and compact dashboard patterns
4. `boneyard` loading-skeleton strategy for stable perceived performance and reduced layout shift
5. `awesome-design-md` design-system references for spacing, hierarchy, typography, and component rhythm

The result should not be a polished version of the current workspace. It should be a different product shape.

Additionally, the proposal now locks a senior-level data-sourcing posture:

- `pandas` is treated as the transformation layer, not a market-data source
- `yfinance` is treated as the primary source for this phase, with explicit reliability caveats
- fundamental and production-critical signals require explicit contracts and provenance tracking
- blind spots and blast radius controls are part of scope, not deferred polish

## What Changes

- Archive the current frontend into `/v0` before any live replacement work begins.
- Replace the active frontend with a new route-based dashboard shell built from scratch around five purpose-built routes:
  - `/portfolio/home`
  - `/portfolio/analytics`
  - `/portfolio/risk`
  - `/portfolio/signals` (visible label: `Opportunities`)
  - `/portfolio/asset-detail/:ticker`
- Make `/portfolio/home` the default opening route and the dominant product surface.
- Preserve only the few existing behaviors that still pay rent:
  - portfolio hierarchy pivot behavior
  - quant report lifecycle surface
  - explicit loading/empty/stale/unavailable/error states
  - reusable typed finance formatting and API utilities where still useful
- Rewrite the design brief so the frontend optimizes for first-viewport clarity and progressive disclosure, not many routes.
- Enforce production-quality frontend engineering standards for:
  - colocated component architecture
  - composition over over-configured wrapper components
  - explicit container/presentation separation where data loading is non-trivial
  - simplest-possible state ownership (`local`, `URL`, `server`) before introducing broader stores
- Enforce storytelling flow at module level so each primary block answers:
  - `what happened`
  - `why it matters`
  - `what to do next`
- Treat accessibility, responsive behavior, and state feedback as implementation contracts, not visual polish:
  - keyboard-accessible interactions
  - semantic headings and labels
  - meaningful loading, empty, and error states
  - mobile-first layouts verified at `320`, `768`, `1024`, and `1440`
- Reject generic AI-default visual patterns:
  - no purple/indigo default branding
  - no arbitrary spacing or raw hex-driven styling in route-level components
  - no oversized card-grid filler layouts
  - no color-only status communication
- Keep unsupported fundamental and proprietary technical metrics explicit as `unavailable` until a real data contract exists.
- Define a source-contract strategy for every key metric family:
  - market bars and watchlist metrics
  - fundamentals and quality ratios
  - technical and risk overlays
- Add a `yfinance` capability matrix so implementation prioritizes metrics that are already obtainable now.
- Add data-provenance, freshness, and confidence states to prevent false precision.
- Preserve and compact the Quant report lifecycle gadget as a compact utility surface embedded in the shell, including:
  - HTML report generation
  - analyst pack export
  - report scope (portfolio vs symbol)
  - report date-range selector
- Add a proportion-based visual system for spacing and panel rhythm using a phi-derived scale (`1.613`) with explicit corner-radius tokens for dense and pill controls.

## Capabilities

### New Capabilities

- `frontend-legacy-archive`
  - stores the pre-redesign frontend under `/v0`
- `frontend-five-route-investing-cockpit`
  - defines a compact personal dashboard with five purpose-built routes and compact utility surfaces
- `frontend-trading-dashboard-llm-wiki`
  - preserves the business logic, metric hierarchy, and UX rules for future LLM planning and implementation

### Modified Capabilities

- `frontend-dashboard-visual-system`
  - changes from executive-workspace framing to a compact, didactic, five-route visual system
- `frontend-analytics-workspace`
  - changes from many route-level surfaces to one purposeful route family with bounded disclosures
- `frontend-workspace-shell-navigation`
  - changes from a heavier persistent shell to minimal chrome subordinate to the active route

### Deprecated Capabilities

- None.

### Removed Capabilities

- None.

## Impact

- OpenSpec artifacts under `openspec/changes/archive-v0-and-build-compact-trading-dashboard/`
- LLM/domain wiki under `docs/product/trading-dashboard-llm-wiki.md`
- Third-pass implementation memo under `docs/product/portfolio-dashboard-third-pass-refinement.md`
- Future live implementation will primarily affect:
  - `frontend/`
  - `docs/guides/frontend-api-and-ux-guide.md`
  - `docs/product/portfolio-kpi-governance.md`
  - `CHANGELOG.md`
