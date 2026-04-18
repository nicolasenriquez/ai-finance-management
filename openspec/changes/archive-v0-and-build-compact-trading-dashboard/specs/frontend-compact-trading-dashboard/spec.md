## ADDED Requirements

### Requirement: The active frontend SHALL center one compact five-route decision shell
The frontend SHALL use one compact route-based shell as the primary product surface, and that shell SHALL expose exactly five primary routes: `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, and `/portfolio/asset-detail/:ticker`.

#### Scenario: One primary shell replaces the large workspace-first experience
- **WHEN** a user opens the active frontend
- **THEN** the primary route or screen presents one compact five-route dashboard rather than a tall multi-surface workspace
- **THEN** the dashboard leads with the current decision state before deeper supporting evidence
- **THEN** the first navigation layer does not expand into many route-like analytical tabs

### Requirement: `/portfolio/home` SHALL be the default landing route
The frontend SHALL open on `/portfolio/home` by default, and that route SHALL be the dominant first-surface decision experience.

#### Scenario: Portfolio state is the first product job
- **WHEN** a user first lands on the dashboard
- **THEN** the default route is `/portfolio/home`
- **THEN** the first viewport emphasizes portfolio state, benchmark comparison, and immediate attention before deeper analysis

### Requirement: `/portfolio/analytics` SHALL provide performance explainability
The frontend SHALL provide one `analytics` route focused on performance, attribution, contribution, and return consistency.

#### Scenario: Performance review stays compact and bounded
- **WHEN** a user opens `/portfolio/analytics`
- **THEN** the first viewport summarizes performance-over-time, attribution, contribution, and rolling context
- **THEN** deeper drill-down surfaces remain available through bounded disclosure patterns

### Requirement: `/portfolio/risk` SHALL provide downside and concentration control
The frontend SHALL provide one `risk` route focused on drawdowns, fragility, correlation, and concentration.

#### Scenario: Risk review stays explicit and bounded
- **WHEN** a user opens `/portfolio/risk`
- **THEN** the first viewport summarizes risk posture, drawdown, distribution, and correlation context
- **THEN** deeper diagnostics remain available through bounded disclosure patterns

### Requirement: `/portfolio/signals` SHALL remain a secondary tactical overlay
The frontend SHALL provide one `signals` route focused on review queues, momentum ranking, tactical signal state, and opportunity discovery. The visible page label MAY render as `Opportunities`.

#### Scenario: Tactical review stays secondary
- **WHEN** a user opens `/portfolio/signals`
- **THEN** the route emphasizes ranked review candidates, signal state, and watchlist items
- **THEN** the visible label can be `Opportunities` while the route slug remains `/portfolio/signals`
- **THEN** the route does not become the dominant product surface

### Requirement: `/portfolio/asset-detail/:ticker` SHALL isolate deep asset review
The frontend SHALL provide one `asset-detail` route focused on ticker-level detail, benchmark-relative context, and tactical price action.

#### Scenario: Candlestick and detailed technicals stay isolated
- **WHEN** a user opens `/portfolio/asset-detail/:ticker`
- **THEN** the route shows OHLC price action, price-volume context, and per-asset risk/detail modules
- **THEN** candlestick treatment is not used on executive routes

### Requirement: The compact dashboard SHALL use progressive disclosure instead of long scroll
The frontend SHALL prefer route changes, segmented controls, drawers, sheets, or other progressive-disclosure patterns over long vertical panel stacking.

#### Scenario: Core meaning is visible above the fold
- **WHEN** a user lands on any executive route on a desktop viewport
- **THEN** the first viewport shows the main decision summary, action state, and dominant supporting module without requiring long downward scrolling
- **THEN** deeper research and evidence remain reachable through bounded disclosure patterns instead of repeated full-height cards

### Requirement: The compact dashboard SHALL preserve explicit action or wait framing
The frontend SHALL make the output of the decision system explicit by presenting action states such as buy, add, wait, avoid, or unavailable as first-surface guidance.

#### Scenario: The dashboard communicates what to do next
- **WHEN** the dashboard renders its overview state
- **THEN** the user can tell whether the current setup is actionable, not actionable, or missing required evidence
- **THEN** the reason for that state is visible in plain language

### Requirement: Missing research contracts SHALL render as unavailable, not invented
If the backend does not expose a true contract for a requested fundamental or technical metric, the frontend SHALL render that surface as unavailable rather than generating demo-only or inferred finance values.

#### Scenario: Unsupported research modules remain trustworthy
- **WHEN** a requested research module depends on metrics such as `P/E`, `Rule of 40`, `J5`, or `volume profile` that are not yet provided by a real API contract
- **THEN** the module renders an explicit unavailable state with guidance about the missing contract
- **THEN** the dashboard does not show fabricated or silently substituted values

### Requirement: Decision-critical metrics SHALL expose provenance and freshness state
The frontend SHALL show source provenance and freshness state for decision-critical metrics so users can distinguish direct data from derived or proxy data.

#### Scenario: Action guidance is downgraded when evidence freshness is weak
- **WHEN** a metric needed for `buy` or `add` state is stale, delayed, or proxy-only
- **THEN** the dashboard visibly marks the metric freshness/confidence state
- **THEN** action guidance degrades to `wait` or `unavailable` with an explicit reason instead of implying high confidence

### Requirement: Module failures SHALL stay localized
The compact dashboard SHALL isolate failures at module level so a provider outage does not collapse the route shell.

#### Scenario: One data provider fails during load
- **WHEN** one module cannot resolve its source contract because of timeout, rate limit, or provider error
- **THEN** only that module enters explicit error or unavailable state
- **THEN** other modules and the rest of the active route remain interactive

### Requirement: Route modules SHALL use compositional, colocated frontend architecture
The frontend SHALL organize route-level modules with colocated implementation and test files, and complex data-loading surfaces SHALL separate data orchestration from presentation rendering.

#### Scenario: A route module grows beyond simple rendering
- **WHEN** a route module needs remote data, lifecycle handling, or route-specific state
- **THEN** the implementation keeps data loading in a container component or hook
- **THEN** presentational components remain focused on rendering and interaction
- **THEN** route-level files do not accumulate unrelated rendering, fetching, and state concerns in one oversized component

### Requirement: Primary routes SHALL satisfy keyboard and semantic accessibility baselines
The compact dashboard SHALL make all primary interactive elements keyboard accessible, preserve visible focus treatment, use semantic headings/labels, and avoid relying on color alone to communicate state.

#### Scenario: A user navigates the dashboard without a pointer
- **WHEN** a user tabs through `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, `/portfolio/signals`, or `/portfolio/asset-detail/:ticker`
- **THEN** all interactive controls are reachable and operable by keyboard
- **THEN** focus remains visible
- **THEN** stateful warnings, gains/losses, and alerts are understandable without color-only encoding

### Requirement: Primary routes SHALL be mobile-first and breakpoint-verified
The compact dashboard SHALL be usable without horizontal overflow at `320`, `768`, `1024`, and `1440` widths, with route density adapting by breakpoint.

#### Scenario: The same route is viewed on narrow and wide screens
- **WHEN** a primary route is rendered on supported viewport widths
- **THEN** layout stays within the viewport without horizontal scrolling
- **THEN** module priority remains legible on mobile-first layouts
- **THEN** dense desktop compositions do not collapse into unreadable stacks on narrow screens

### Requirement: Primary modules SHALL render meaningful loading, empty, and error states
The compact dashboard SHALL provide explicit loading, empty, unavailable, and error states for primary modules, with stable geometry that reduces layout shift.

#### Scenario: A module loads slowly or resolves no usable data
- **WHEN** a primary module is waiting on data, receives no data, or hits a recoverable error
- **THEN** the module renders a meaningful skeleton, empty, unavailable, or error state
- **THEN** the route preserves layout stability instead of collapsing or jumping
- **THEN** the user can understand what happened and whether retry or follow-up action is available

### Requirement: Route-level styling SHALL use semantic tokens and avoid generic AI-default patterns
The compact dashboard SHALL use semantic design tokens for color, spacing, typography, border, and radius decisions on route-level surfaces, and SHALL avoid arbitrary styling patterns that undermine the intended financial product identity.

#### Scenario: A new route module is introduced
- **WHEN** a new route-level module or component is implemented
- **THEN** it uses semantic tokens instead of raw hex values and off-scale spacing
- **THEN** it avoids decorative hero filler, maximum-radius-everywhere card styling, and generic purple-first visual language
- **THEN** the resulting surface remains consistent with the product's compact, executive visual system

### Requirement: Primary modules SHALL follow a didactic storytelling contract
The compact dashboard SHALL encode each primary module using a compact storytelling sequence: `what`, `why`, `action`, and `evidence`.

#### Scenario: Decision cards are interpretable without external coaching
- **WHEN** a user reads a primary module on any route
- **THEN** the module explicitly states the current metric or state (`what`)
- **THEN** the module explains interpretation in plain language (`why`)
- **THEN** the module provides a clear recommendation (`action`)
- **THEN** the module exposes source/freshness confidence context (`evidence`)

### Requirement: The compact dashboard SHALL preserve a compact Quant report utility
The compact dashboard SHALL preserve report lifecycle actions with bounded density, including HTML generation, analyst-pack export, scope selection, and date-range selection, but SHALL not make reports a primary route.

#### Scenario: Report actions remain available without bloating first viewport
- **WHEN** a user opens the dashboard shell or an asset-detail view
- **THEN** a compact report utility provides `Generate HTML report` and `Export analyst pack (.md)` actions
- **THEN** the utility includes scope controls (`portfolio` and symbol-level selection) and a report date-range selector
- **THEN** lifecycle states remain explicit (`requested`, `generated`, `preview ready`, `error`, `unavailable`)
