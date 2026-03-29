## 1. Investigation and KPI Contract Lock

- [ ] 1.1 Audit current Home/Analytics/Risk chart modules for duplication, spacing drift, and report-action coupling points.
  Notes:
  - Record exact component-level duplication findings and target consolidation paths before code changes.
- [ ] 1.2 Define the analyst-owned KPI catalog and route placement matrix (`Home`, `Analytics`, `Risk`, `Quant/Reports`) in docs/change artifacts.
  Notes:
  - Capture KPI name, interpretation narrative, formula notes, and single route owner for each promoted KPI.
- [ ] 1.3 Confirm scope boundaries for dedicated `Quant/Reports` workflow and route entry semantics with existing workspace navigation contracts.
  Notes:
  - Keep deterministic route behavior and avoid introducing hidden redirects from existing deep links.

## 2. Fail-First Test Baseline

- [ ] 2.1 Add fail-first frontend tests that reproduce current chart duplication/spacing inconsistencies across workspace routes.
  Notes:
  - Prefer route-level tests tied to shared chart primitives so regressions fail deterministically.
- [ ] 2.2 Add fail-first frontend tests that reproduce Home-coupled report workflow behavior expected to move to dedicated `Quant/Reports` surface.
  Notes:
  - Assert explicit loading/error/unavailable/ready states and keyboard-triggered interactions.
- [ ] 2.3 Add fail-first backend/API contract tests for route-agnostic Quant report generation/retrieval workflows and explicit lifecycle metadata.
  Notes:
  - Verify requests do not require Home-specific context fields and reject implicit defaults.

## 3. Backend and Contract Alignment

- [ ] 3.1 Update portfolio analytics schemas/contracts to expose deterministic scope and lifecycle metadata needed by promoted Quant/Reports UX.
- [ ] 3.2 Refactor relevant report service/route logic to remain route-agnostic and fail explicitly for invalid scope or unavailable artifacts.
- [ ] 3.3 Update backend tests for promoted workflow contracts, including invalid-state failures and read-only side-effect boundaries.

## 4. Frontend IA and Chart Composition Implementation

- [ ] 4.1 Implement dedicated `Quant/Reports` workspace surface (or promoted equivalent) and wire navigation from existing workspace layout.
  Notes:
  - Keep Home as executive snapshot route; report generation entry points should direct users to dedicated analytical context.
- [ ] 4.2 Refactor chart modules to use one shared composition contract (container sizing, spacing tokens, shared header semantics) across Home/Analytics/Risk.
- [ ] 4.3 Remove duplicated route-local chart wrappers and align module placement with KPI ownership matrix.
- [ ] 4.4 Integrate explicit report workflow states and accessibility labeling in promoted Quant/Reports UI controls and previews.
- [ ] 4.5 Extend frontend tests for route navigation determinism, chart composition consistency, and report workflow lifecycle handling.

## 5. Documentation and Governance Updates

- [ ] 5.1 Update product and frontend guide docs with finalized KPI matrix, route IA, and Quant/Reports workflow boundaries.
- [ ] 5.2 Update OpenSpec deltas (if implementation-driven refinements emerge) so specs remain implementation-accurate before closeout.
- [ ] 5.3 Add `CHANGELOG.md` entry summarizing Phase F behavior changes, files touched, and validation evidence.

## 6. Validation and Closeout

- [ ] 6.1 Run backend quality gates and targeted portfolio analytics tests for report-contract changes.
- [ ] 6.2 Run frontend gates (`lint`, `test`, `build`) including updated workspace route and report-flow test suites.
- [ ] 6.3 Run OpenSpec validation for the Phase F change and all specs, then record pass/fail evidence in changelog and artifacts.
