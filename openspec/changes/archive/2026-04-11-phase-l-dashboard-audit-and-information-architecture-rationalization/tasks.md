## 1. Dashboard Audit Baseline

- [x] 1.1 Create a complete widget inventory for `Home`, `Analytics`, `Risk`, `Quant/Reports`, and `Transactions` with question/decision/source metadata.
- [x] 1.2 Produce heuristic and visualization audit findings with severity (`low/medium/high`) and impact notes.
- [x] 1.3 Classify every inventoried widget as `KEEP`, `MERGE`, `MOVE`, or `REMOVE` and freeze rationale before UI refactors.
- [x] 1.4 Publish route-to-lens mapping (`Overview`, `Holdings`, `Performance`, `Cash/Transactions`) and textual wireframes for each primary route.

## 2. Fail-First UI Composition and Shell Contracts

- [x] 2.1 Add fail-first tests for route-level dominant primary job and bounded first-surface module counts.
- [x] 2.2 Add fail-first tests that prevent duplicate equal-priority visuals for the same analytical question on one route.
- [x] 2.3 Add fail-first tests for route-aware shell density behavior and deterministic mode persistence across navigation.
- [x] 2.4 Add fail-first tests proving progressive disclosure behavior for advanced modules on high-density routes.

## 3. Route Composition Rationalization

- [x] 3.1 Implement shell density modes in shared workspace layout primitives and apply route policies.
- [x] 3.2 Refactor `Home` into a strict highlights-first overview surface with secondary drill-down modules.
- [x] 3.3 Refactor `Analytics`, `Risk`, and `Quant/Reports` to remove or demote redundant visuals and enforce progressive disclosure boundaries.
- [x] 3.4 Refactor `Transactions` to align with `Cash/Transactions` lens framing and concise operating narrative.
- [x] 3.5 Update workspace navigation labels and contextual copy to reflect four monitoring lenses without breaking current route compatibility.

## 4. Governance, Explainability, and Documentation

- [x] 4.1 Extend KPI/widget governance artifacts to include question ownership, decision tags, and benchmark/comparison framing.
- [x] 4.2 Document all `MERGE/MOVE/REMOVE` outcomes with severity/rationale and replacement destination behavior.
- [x] 4.3 Update design/UX guides with the new audit framework, route budgets, and progressive-disclosure rules.
- [x] 4.4 Update `CHANGELOG.md` with dashboard IA rationalization scope and evidence links.

## 5. Validation and Implementation Handoff

- [x] 5.1 Run frontend validation gates (`lint`, `type-check`, `test`, `build`) for all touched dashboard routes.
- [x] 5.2 Run relevant backend contract checks if any frontend assumptions require payload-shape confirmation.
- [x] 5.3 Re-run OpenSpec status/validation checks and confirm artifact completeness.
- [x] 5.4 Capture implementation handoff notes with unresolved risks, regression watchpoints, and acceptance evidence.
