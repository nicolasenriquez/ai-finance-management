## Context

The repository already ships analytics workspace routes, risk estimators, and a first QuantStats-backed endpoint, but runtime behavior is not yet resilient under real data conditions. The current integration can fail the entire Home route due to optional quant call mismatches, and governance documentation does not yet define a dedicated QuantStats standard for adapter behavior, report generation, and frontend placement.

This change is cross-cutting across backend analytics services, frontend route-state handling, standards documentation, and OpenSpec capability contracts. It must preserve repository principles: deterministic contracts, fail-fast semantics, strict typing, and explicit state handling.

## Goals / Non-Goals

**Goals:**
- Define a canonical repository standard for QuantStats usage and constraints.
- Make QuantStats metric integration version-compatible and resilient, especially for optional benchmark-relative metrics.
- Introduce bounded HTML tearsheet reporting as a deliberate capability with explicit scope and error semantics.
- Keep Home route core context available when optional quant/report modules fail.
- Clarify metric placement between Home preview, Risk view, and dedicated Quant/reporting surface.

**Non-Goals:**
- Replacing canonical baseline risk estimators with QuantStats-only implementations.
- Introducing arbitrary strategy backtesting scope.
- Shipping uncontrolled report persistence or cross-user report sharing.
- Reworking unrelated analytics routes or redesigning the full visual system.

## Decisions

### Decision 1: Introduce a QuantStats adapter contract with explicit callable registry
- Decision: use a backend adapter registry that maps metric IDs to verified call paths for the pinned QuantStats version and validates availability during test/runtime preflight.
- Rationale: direct callable assumptions are fragile across versions; adapter mapping keeps behavior explicit.
- Alternatives considered:
  - Direct free-form `getattr` calls per metric: rejected due runtime breakage risk.
  - Static precomputed metrics only (no runtime QuantStats): rejected because it blocks reporting and flexible quant expansion.

### Decision 2: Treat benchmark-relative quant metrics as optional, not hard blockers
- Decision: alpha/beta-style metrics are emitted only when benchmark series and compatible call paths are both available; otherwise explicit omission metadata is allowed without failing all quant metrics.
- Rationale: benchmark-relative signals are useful but non-critical compared with core portfolio context.
- Alternatives considered:
  - Full-endpoint failure when benchmark metrics are unavailable: rejected because it degrades Home reliability.
  - Silent fallback values (`0`, `null` without explanation): rejected by fail-fast/explicit-state principles.

### Decision 3: Add bounded HTML report generation as a dedicated capability
- Decision: expose report generation as explicit API behavior with deterministic scope (`portfolio`, `symbol`, or selected ETF proxy), explicit validation, and controlled output lifecycle.
- Rationale: report generation is materially different from metric retrieval and requires clearer operational boundaries.
- Alternatives considered:
  - Embedding full HTML report generation into Home fetch path: rejected for latency and reliability impact.
  - Frontend-only report generation: rejected due dependency and trust-boundary concerns.

### Decision 4: Enforce section-scoped failure boundaries in Home
- Decision: Home core context (summary/trend/hierarchy) remains available even when optional quant/report modules fail, with explicit section-level error states.
- Rationale: preserves operator visibility while keeping failure explicit.
- Alternatives considered:
  - Keep single page-level error gate for all modules: rejected due coupling and poor resilience.

### Decision 4.1: Freeze metric placement matrix across Home, Risk, and Quant/report surfaces
- Decision:
  - Home: high-signal KPI context + supplemental quant preview only.
  - Risk: interpretation-sensitive risk metrics (drawdown/volatility/beta + methodology context).
  - Quant/report route: expanded quant diagnostics and report-generation actions.
- Rationale: prevents semantic drift and keeps risk interpretation in the correct UX context.
- Alternatives considered:
  - Flat all-metrics-on-Home layout: rejected due overload and reliability coupling.
  - Risk-only quant visibility: rejected due analyst workflow need for quick preview/report entry.

### Decision 4.2: Surface benchmark omissions and report lifecycle states explicitly in frontend
- Decision:
  - Home quant/report modules render omission context from `benchmark_context` when optional benchmark-relative metrics are unavailable.
  - Report-generation UI renders explicit generation and retrieval lifecycle states (`loading`, `error`, `ready`) without replacing page-level core context.
- Rationale: preserves fail-fast transparency while avoiding ambiguity between unavailable optional metrics and successful metric computation.
- Alternatives considered:
  - Silent omission of optional benchmark metrics: rejected because it violates explicit-state guidance.
  - Global page-level error on report action failure: rejected because report actions are optional modules.

### Decision 5: Publish `quantstats-standard` in `docs/standards`
- Decision: create `docs/standards/quantstats-standard.md` and align docs index + changelog obligations.
- Rationale: dependency policy and usage semantics need a single source of truth similar to NumPy/pandas/SciPy standards.
- Alternatives considered:
  - Only updating ADR snippets: rejected because implementation teams need operational rules in standards set.

## Risks / Trade-offs

- [Risk] QuantStats API drift across versions can break adapter assumptions.
  Mitigation: exact pinning, adapter compatibility tests, explicit callable registry checks.

- [Risk] Section-scoped resilience could hide important quant failures.
  Mitigation: show explicit section-level error banners with retry and factual failure reasons.

- [Risk] HTML report generation may increase backend latency and disk churn.
  Mitigation: bounded generation scope, explicit output retention policy, and deterministic cleanup lifecycle.

- [Risk] Ambiguous metric placement (Home vs Risk vs Quant report) can confuse users.
  Mitigation: publish placement matrix in standard and frontend docs; enforce route-level labels.

## Migration Plan

1. Publish standards and OpenSpec contracts before backend/frontend implementation changes.
2. Add fail-first tests for QuantStats adapter compatibility and Home section-scoped state handling.
3. Implement backend adapter and report endpoints behind explicit validation contracts.
4. Implement frontend section-scoped rendering and report actions.
5. Run full validation gates and document evidence in changelog.
6. Rollback strategy: disable new report routes/UI entry points and revert adapter changes while retaining baseline analytics/risk kernels.

## Open Questions

None.
