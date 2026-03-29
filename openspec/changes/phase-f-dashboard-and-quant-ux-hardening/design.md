## Context

The portfolio workspace now has functional Home, Analytics, Risk, and Transactions routes, plus Quant report generation/retrieval contracts. However, dashboard composition still shows route-to-route inconsistency (duplicated chart modules, uneven spacing/sizing behavior), and report actions remain semantically coupled to Home despite a roadmap decision to promote report workflows into a dedicated analytical context.

Phase F is a cross-cutting frontend + contract alignment slice. It touches route information architecture, frontend composition primitives, API consumption boundaries for report workflows, and release-readiness evidence gates. The implementation must preserve repository constraints: fail-fast behavior, explicit state rendering, strict typing, deterministic route contracts, and accessibility-first controls.

## Goals / Non-Goals

**Goals:**
- Deliver an analyst-owned KPI placement model that fixes route intent boundaries (`Home`, `Analytics`, `Risk`, `Quant/Reports`).
- Eliminate chart duplication and spacing drift by standardizing reusable chart composition primitives.
- Promote Quant report workflows to a dedicated workspace surface with explicit lifecycle state handling.
- Keep backend report APIs route-agnostic so UX relocation does not require Home-coupled contracts.
- Extend release-readiness gates to verify chart-consistency and promoted Quant/Reports interaction behavior.

**Non-Goals:**
- Redesigning or replacing backend quant computation methodology.
- Replacing the chart library (`Recharts`) or initiating framework migration work.
- Broad visual-brand redesign outside workspace IA and chart consistency scope.
- Adding cross-user report persistence or long-lived report artifact storage beyond existing bounded lifecycle.

## Decisions

### Decision 1: Introduce a dedicated `Quant/Reports` route surface in workspace IA
- Decision: Treat report generation/retrieval as a first-class workspace surface (or explicitly promoted equivalent), not as an embedded Home-owned workflow.
- Rationale: report tasks are analytical workflows with distinct state transitions and should not compete with Home snapshot comprehension.
- Alternatives considered:
  - Keep report actions on Home and improve copy only: rejected due continued route-purpose ambiguity.
  - Move report actions to Risk: rejected because reports span broader analytical usage than risk-only interpretation.

### Decision 2: Enforce a route-scoped KPI governance catalog before UI reshaping
- Decision: Require a documented KPI matrix with analyst ownership, formula narrative, and route placement prior to implementation finalization.
- Rationale: visual cleanup without KPI ownership often reintroduces duplication and semantic drift in later slices.
- Alternatives considered:
  - Allow implementation-first KPI decisions: rejected due high rework risk.
  - Keep KPI ownership implicit in component names: rejected because it is not auditable or testable.

### Decision 3: Standardize chart composition via shared primitives and tokenized layout contracts
- Decision: Define one chart composition contract for container sizing, spacing, and module headers shared across Home/Analytics/Risk.
- Rationale: deterministic UI contracts reduce duplication and make regression tests reliable.
- Alternatives considered:
  - Route-local chart wrappers per page: rejected because it preserves inconsistency and duplicated logic.
  - One large monolithic chart shell for all routes: rejected due low flexibility for route-specific narratives.

### Decision 4: Keep report API contracts route-agnostic and explicitly stateful
- Decision: backend report endpoints remain independent of Home-specific context and provide explicit scope/lifecycle metadata for dedicated Quant/Reports rendering.
- Rationale: frontend IA changes should not require endpoint redefinition or hidden route assumptions.
- Alternatives considered:
  - Introduce Home-origin flags in API requests: rejected due unnecessary coupling.
  - Infer report lifecycle from missing fields client-side: rejected by explicit-state/fail-fast rules.

### Decision 5: Add release-readiness gates specific to Phase F risks
- Decision: release validation must include chart-consistency checks and dedicated Quant/Reports state + accessibility coverage.
- Rationale: baseline lint/build/test passing is insufficient for this slice’s UX contract risks.
- Alternatives considered:
  - Rely on manual QA only: rejected due low repeatability and weak change evidence.

## Risks / Trade-offs

- [Risk] KPI governance review can slow implementation throughput.
  Mitigation: lock a minimum viable KPI catalog first, then iterate with explicit follow-up tasks.

- [Risk] Promoting a new workspace surface may increase navigation complexity.
  Mitigation: keep deterministic route labels and preserve existing deep-link behavior.

- [Risk] Chart standardization can cause layout regressions in edge viewport sizes.
  Mitigation: add targeted responsive tests and include route-level visual evidence capture in validation.

- [Risk] Existing report interactions may rely on Home-local assumptions hidden in frontend state hooks.
  Mitigation: add fail-first tests that reproduce current coupling before refactoring hooks and API clients.

## Migration Plan

1. Lock spec and KPI governance artifacts for Phase F before implementation starts.
2. Add fail-first frontend/backend tests that capture current chart duplication, spacing inconsistency, and Home-coupled report flow behavior.
3. Refactor workspace routing and composition primitives to introduce dedicated Quant/Reports context and shared chart layout contracts.
4. Update API client/hook layers to consume report contracts from route-agnostic flows.
5. Run frontend/backend/OpenSpec validation gates and capture evidence artifacts.
6. Rollback strategy: disable new route exposure and restore prior workspace composition while retaining backward-compatible report endpoints.

## Open Questions

None.
