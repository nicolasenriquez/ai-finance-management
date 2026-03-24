# Frontend MVP PRD Addendum

## Purpose

This addendum defines the frontend MVP contract for portfolio analytics delivery.
It aligns product intent with the current backend reality: a ledger-first analytics API that is implemented and read-only.

This document is additive to:

- `docs/product/prd.md`
- `docs/product/roadmap.md`
- `docs/product/decisions.md`
- `docs/guides/portfolio-ledger-and-analytics-guide.md`

## Current Backend Contract Baseline

As of 2026-03-23, the frontend contract depends on:

- `GET /api/portfolio/summary`
- `GET /api/portfolio/lots/{instrument_symbol}`
- Explicit ledger consistency metadata: `as_of_ledger_at`
- Ledger-only KPI v1 fields (`open_*`, `realized_*`, `dividend_*`)
- Deterministic symbol handling (trim + uppercase), with explicit unknown-symbol rejection

## Product Constraints

- Ledger-first truth is non-negotiable.
- Frontend views are derived, not authoritative.
- Analytics API calls are read-only and must not trigger rebuild side effects.
- Missing upstream data must fail clearly, never silently.
- Market-data-dependent valuation remains deferred.

## Scope Reconciliation With PRD

`docs/product/prd.md` keeps "No advanced UI/UX polish in MVP" as a non-goal.
This addendum does not override that boundary. It clarifies the required baseline:

- Required now: professional usability, accessibility, deterministic behavior, and visual consistency.
- Deferred: advanced visual storytelling, extensive customization/theming engines, and chart-heavy exploratory UX.

Interpretation for implementation:

- "No advanced polish" means avoid expanding scope for novelty.
- It does not permit low-quality or ambiguous UX for core analytics workflows.

## Frontend MVP Goals

- Present a trustworthy grouped portfolio summary by instrument.
- Provide explainable lot-level drill-down per instrument.
- Make ledger snapshot time obvious (`as_of_ledger_at`).
- Prioritize auditability, clarity, and deterministic behavior over visual novelty.

## In Scope

- Portfolio summary table view by symbol.
- Lot-detail view for a selected symbol.
- Deterministic formatting of quantities, money, and symbols.
- Explicit handling for loading, empty, and error states.
- Responsive desktop-first layout that remains usable on mobile.
- Accessibility-first interaction model (keyboard and screen reader compatible).
- A restrained light/dark theme toggle if it remains token-driven and does not expand into a general theming system.

## Out of Scope

- Authentication and multi-user workflows.
- AI/agentic UX features.
- Market value, unrealized price-based metrics, and FX-sensitive valuation.
- Portfolio charting that implies unsupported market-data precision.
- Advanced personalization and theming systems.

## Primary User Jobs

- Understand open position and realized/dividend history by instrument.
- Drill into lots to verify how positions were built and consumed.
- Trust response freshness through visible ledger timestamp context.
- Detect unsupported cases quickly from explicit error messaging.

## Functional Requirements

- Summary page must request `GET /api/portfolio/summary` and render one row per symbol.
- Lot detail must request `GET /api/portfolio/lots/{instrument_symbol}` from a summary interaction.
- Symbol rendering must use canonical uppercase in UI labels.
- Decimal precision must preserve backend meaning:
  - quantity-like fields display up to 9 decimal places
  - money-like fields display 2 decimal places
- Every analytics surface must show the `as_of_ledger_at` timestamp context.

## UX Requirements

- The default landing state communicates "ledger-backed portfolio summary".
- Row-to-detail interaction is obvious and keyboard accessible.
- Unknown symbol paths must produce explicit not-found messaging.
- Error copy must be factual, concise, and actionable.
- Empty states must clarify whether data is missing versus unsupported.

## Non-Functional Requirements

- Accessibility target: WCAG 2.2 AA baseline.
- Performance target: Core Web Vitals "good" thresholds for key views.
- Reliability target: deterministic rendering from typed API payloads without hidden client-side inference.

## MVP Success Criteria

- User can load summary and inspect lot detail without ambiguity.
- UI reflects only supported ledger-derived KPIs.
- Error and edge-state behavior is explicit and consistent.
- Accessibility and performance gates pass for the frontend scope.
- Documentation and acceptance checklist are complete before UI implementation broadens.
