# DESIGNS.md
Version: 0.3
Date: 2026-04-05
Product: AI Finance Management
Design Intent: Ledger-first portfolio analytics workspace for a passive investor
Primary Surface: Web dashboard (React + Vite)
Consumers: Human designers, frontend engineers, coding agents, UI generation agents

---

## 1. Purpose

This document upgrades the earlier design proposal into a codebase-aligned design contract.
It defines what the current product should look and feel like based on implemented routes,
backend contracts, and repository standards.

This is a design alignment document, not a replacement for code contracts.

---

## 2. Source-of-Truth And Precedence

When design intent conflicts with implementation constraints, follow this order:

1. Backend and frontend typed contracts in code
2. Repository standards
3. Product docs and roadmap
4. This file

Primary companion docs:

- `docs/standards/frontend-standard.md`
- `docs/standards/portfolio-visualization-standard.md`
- `docs/guides/frontend-design-system-guide.md`
- `docs/guides/frontend-api-and-ux-guide.md`

---

## 3. Product Posture

The product is a passive-investor analytics workspace.

Design must optimize for:

- long-horizon monitoring
- benchmark-aware interpretation
- concentration and diversification visibility
- downside and recovery context
- deterministic explainability from ledger truth

The product is not:

- an intraday trading terminal
- an execution workflow
- a speculative signal board

---

## 4. Current Information Architecture (Implemented)

As of 2026-04-05, the primary routes are:

- `/portfolio/home`
- `/portfolio/analytics`
- `/portfolio/risk`
- `/portfolio/reports`
- `/portfolio/transactions`
- `/portfolio/copilot`
- `/portfolio/:symbol` (lot detail)

Design decisions must preserve this IA unless route changes are explicitly approved.

---

## 5. Backend Contract Map (Implemented)

### Portfolio analytics endpoints

- `GET /api/portfolio/summary`
- `GET /api/portfolio/lots/{instrument_symbol}`
- `GET /api/portfolio/time-series`
- `GET /api/portfolio/contribution`
- `GET /api/portfolio/risk-estimators`
- `GET /api/portfolio/risk-evolution`
- `GET /api/portfolio/return-distribution`
- `GET /api/portfolio/efficient-frontier`
- `POST /api/portfolio/monte-carlo`
- `GET /api/portfolio/health-synthesis`
- `GET /api/portfolio/quant-metrics`
- `POST /api/portfolio/quant-reports`
- `GET /api/portfolio/quant-reports/{report_id}`
- `GET /api/portfolio/hierarchy`
- `GET /api/portfolio/transactions`

### Portfolio ML endpoints

- `GET /api/portfolio/ml/signals`
- `GET /api/portfolio/ml/forecasts`
- `GET /api/portfolio/ml/registry`

### Copilot endpoint

- `POST /api/portfolio/copilot/chat`

---

## 6. Core UX Rules (Codebase-Aligned)

### 6.1 Ledger-first trust

- Show ledger freshness (`as_of_ledger_at`) on analytics surfaces.
- Keep provenance visible (snapshot keys, report lifecycle, state banners).

### 6.2 Fail-fast UI states

- Every async module must support loading, ready, empty/unavailable, and error.
- Unsupported scope/symbol combinations must render explicit factual messages.

### 6.3 Deterministic behavior

- Do not invent missing metrics client-side as if they were backend truth.
- If a view derives helper metrics from API rows, label them as derived.

### 6.4 Explainability over novelty

- Each chart/card needs a clear analytical purpose.
- Titles, subtitles, and metric explainability affordances are required in core modules.

### 6.5 Route-first focus

- First viewport must show route title, trust context, controls, and primary module.
- Avoid hero-style marketing framing on analytics routes.

---

## 7. Route-Level Design Contracts

### `/portfolio/home` (executive snapshot)

Must prioritize:

- portfolio operating posture
- trend preview with benchmark context
- hierarchy/allocation snapshot
- health synthesis context and trust signals
- deterministic drill-down to analytics/risk/reports/transactions

### `/portfolio/analytics` (performance + attribution)

Must prioritize:

- trend analysis
- contribution concentration and top movers
- attribution explanation (including waterfall-style decomposition)

### `/portfolio/risk` (risk interpretation)

Must prioritize:

- estimator cards with methodology metadata
- drawdown timeline
- rolling volatility/beta timeline
- return distribution and tail context
- mixed-unit guardrails

### `/portfolio/reports` (advanced diagnostics + lifecycle)

Must prioritize:

- quant metric scorecards and benchmark context
- report generation/retrieval lifecycle
- Monte Carlo controls/results
- efficient frontier context
- monthly-return heatmap-style view where supported

### `/portfolio/transactions` (ledger history)

Must prioritize:

- deterministic event list
- explicit v1 scope messaging (ledger events only)
- lightweight filtering and no market-refresh diagnostics in this route

## 7.1 Phase-L IA Governance Addendum

- Each route must declare one dominant first-surface analytical question.
- First-surface primary module budget is capped at 7 modules.
- Duplicate equal-priority visuals for the same analytical question are disallowed.
- High-density routes (`Risk`, `Quant/Reports`) must gate advanced diagnostics behind explicit progressive-disclosure controls.
- Shell density is route-aware and deterministic (`expanded`, `balanced`, `compact`) so auxiliary chrome does not dominate first-view analysis.

### `/portfolio/copilot` (read-only assistant)

Must prioritize:

- chat-first prompt composition
- typed state handling (`ready/blocked/error` style UX)
- evidence and limitation visibility
- deterministic opportunity candidate table separate from AI narration
- continuity between docked launcher and expanded copilot route

### `/portfolio/:symbol` (lot detail)

Must prioritize:

- lot explainability
- deterministic symbol handling
- continuity from summary/hierarchy drill-down flows

---

## 8. Chart And Module Selection Rules (Current Data Reality)

Use only chart types that match available contracts.

### Supported core mappings

- Time series -> line/area trend with benchmark overlays where provided
- Contribution -> ranked horizontal bars and attribution waterfall
- Risk evolution -> drawdown line + rolling estimators
- Return distribution -> histogram/bucket bars
- Efficient frontier -> frontier/asset relationship visualization
- Monthly returns view -> derived heatmap-style summary with explicit caveat text

### Avoid promoting as primary surfaces unless contracts exist

- candlesticks
- multi-axis visuals with unclear unit semantics
- gauge/speedometer widgets
- dense sparkline walls without task prioritization
- crypto-trader style control panels

---

## 9. Data Semantics And Unit Integrity

Design and formatting must preserve backend units:

- Money fields remain currency values.
- `percent` metrics are displayed as percent and must not be re-scaled incorrectly.
- `ratio` metrics may be percent-formatted only at explicit formatting boundaries.
- Axis labels and tooltips must declare units where ambiguity is possible.

Do not infer unavailable dimensions as if implemented:

- No dedicated asset-class/geography/currency/crypto taxonomies unless present in contracts.

---

## 10. Interaction Contracts

### 10.1 Period control

Supported period enum in current frontend/backend contracts:

- `30D`, `90D`, `6M`, `252D`, `YTD`, `MAX`

### 10.2 Scope control

Where supported:

- `portfolio`
- `instrument_symbol`

`instrument_symbol` inputs should be normalized (trim + uppercase) before request dispatch.

### 10.3 Drill-down model

Primary pathway:

- Home summary/hierarchy -> symbol route (`/portfolio/:symbol`)
- Home -> Analytics/Risk/Reports/Transactions for deeper interpretation

### 10.4 Error and empty states

- Use factual copy: what failed, why (if known), and what user can do next.
- Keep retry actions visible for recoverable failures.

---

## 11. Visual Language

Use a calm, high-contrast, finance-professional style:

- restrained palette with semantic tokens
- dense but readable layouts
- strong numeric legibility
- minimal decorative motion

For copilot-specific surfaces, use a familiar chat-shell structure:

- compact persistent header with explicit chat context
- right-side docked launcher on desktop
- full-screen modal panel on mobile
- expanded route with conversation timeline + message composer as primary block
- deterministic insights (evidence, limitations, candidates) as secondary blocks

Typography and spacing should follow the existing design-system guidance:

- readable table-first hierarchy
- tabular numerals for KPI/dense numeric regions
- compact headers on workspace routes

---

## 12. Accessibility And Performance Gates

Design decisions must satisfy:

- WCAG 2.2 AA baseline
- visible keyboard focus
- color use not dependent on red/green only
- reduced-motion support
- route-level loading/error/empty clarity
- Core Web Vitals target profile from frontend standards

No design change is complete without evidence alignment in the repository workflow.

---

## 13. Non-Goals (Current Scope)

Not in current primary design scope:

- trading execution workflows
- real-time terminal UX
- order-routing interfaces
- dedicated standalone crypto page as a separate app experience
- novelty-first chart galleries without deterministic contract backing

---

## 14. Deferred And Conditional Extensions

The following ideas remain valid but deferred until contracts/IA are approved:

- standalone holdings page separate from current route flow
- standalone crypto page with category taxonomy
- geography/currency/allocation modules requiring new backend dimensions
- advanced factor-map/scenario modules beyond current risk/report contracts

Any extension must:

1. land API contract first,
2. define units/provenance/failure semantics,
3. add route/module tests and evidence.

---

## 15. Agent Implementation Guidance

When generating or modifying UI, follow this order:

1. Start from route job-to-be-done.
2. Bind module choice to existing endpoint contracts.
3. Preserve ledger trust context and explicit state handling.
4. Preserve deterministic semantics and unit correctness.
5. Prefer clarity/comparability over decorative complexity.
6. If data is unavailable, render explicit unavailable state instead of fallback fabrication.

If a proposed visualization cannot be backed by current contracts, classify it as deferred.

---

## 16. Copilot Chat Experience Contract (Current Frontend)

The current codebase-aligned copilot presentation is:

- `WorkspaceCopilotLauncher` for persistent workspace entry
- docked desktop chat panel + mobile full-screen panel
- `WorkspaceCopilotComposer` as a shared chat timeline/composer surface
- `/portfolio/copilot` as expanded chat route using the same session continuity

Design changes to copilot should preserve:

1. shared state continuity across docked and expanded modes
2. read-only safety language and typed state visibility
3. explicit evidence and limitation rendering
4. deterministic opportunity candidates shown separately from AI narration
