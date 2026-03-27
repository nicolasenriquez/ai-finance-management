## Context

The repository already has three distinct verification weights for market-refresh behavior:

- default integration runs that exclude heavy market-scope lanes
- a heavy `100` integration lane
- a very-heavy `200` integration lane

It also already contains a lighter representative smoke test that exercises `core` plus a small deterministic non-core sample. The operational problem is not the absence of broader-than-core coverage; it is that the documented readiness posture still leans too heavily on long-running full-scope refresh validation for local development machines that cannot sustain that cost comfortably.

The current Phase 6 docs still frame `core -> 100` live smoke as the active closeout path and keep `200` as deferred follow-up scope. In practice, the repo already shows a more sustainable shape:

- `core` is the only scope directly tied to current portfolio truth
- broader-than-core validation can be approximated with a deterministic representative sample
- full `100` and especially `200` create material runtime and CPU pressure under current sequential request pacing

This change is intentionally about verification posture, not market-refresh semantics. The existing persistence boundary, snapshot identity model, and bounded provider recovery rules remain unchanged.

## Goals / Non-Goals

**Goals:**

- Keep `core` as the required live verification path for current operator readiness.
- Reframe broader-than-core validation around a deterministic representative non-core smoke lane.
- Remove routine `200` verification from current local validation expectations.
- Keep full-scope `100` available only as explicit manual/soak coverage rather than default readiness evidence.
- Align tests, `just` commands, validation docs, and product planning docs with the lighter verification contract.

**Non-Goals:**

- Changing refresh persistence semantics, snapshot-key identity, or idempotent write behavior.
- Adding incremental backfill or watermark-based “fetch only the missing tail” logic.
- Expanding market-data analytics, KPI contracts, or frontend valuation behavior.
- Broadening currency fallback rules beyond the currently documented missing-metadata default-currency behavior.
- Adding scheduler, queue, worker, or public market-data API infrastructure.

## Decisions

### Decision: Keep `core` as the only required live operational readiness gate

`core` is the scope anchored to the current required portfolio symbols, so it remains the only live refresh path that must stay in the routine readiness contract. This preserves the direct connection between market-refresh verification and the portfolio the product actually depends on now.

Alternative considered:

- Keep `core -> 100` as the routine live gate. Rejected because it continues to bind routine readiness to a scope that is broader than the current portfolio truth and is operationally expensive on constrained local machines.

### Decision: Promote representative non-core smoke coverage instead of full-scope expansion by default

The repo already has a deterministic PR-smoke pattern that combines `core` with a small non-core sample. That existing seam should become the default broader-than-core safeguard because it preserves non-core contract coverage without forcing the full runtime cost of `100` or `200`.

Alternative considered:

- Replace `100` with a renamed smaller pseudo-`100` scope such as `30` or `50`. Rejected because it would overload the current scope names and blur the meaning of the symbol-universe contract.

### Decision: Retain full `100` only as optional manual soak coverage

Full-scope `100` still has value when deliberately testing refresh tuning or provider stability, but it should no longer be treated as routine local readiness evidence. The repo should keep the lane available only when an operator intentionally chooses that heavier coverage.

Alternative considered:

- Remove `100` entirely. Rejected because it would eliminate a useful bounded soak lane for targeted provider/runtime investigation.

### Decision: Remove routine `200` verification from the current contract

`200` adds the most runtime pressure and is already documented as deferred follow-up scope. This change should make that practical reality explicit by removing `200` from routine validation and readiness expectations rather than leaving it as a lingering nominal lane.

Alternative considered:

- Keep `200` as a dormant but documented manual lane. Rejected because that still invites accidental coupling between current readiness and a scope the repo does not intend to sustain now.

### Decision: Keep refresh semantics unchanged in this change

The user’s incremental “fill only missing dates” idea is valid, but it changes refresh semantics, snapshot meaning, and evidence interpretation. That belongs in a separate proposal after verification burden is reduced and the team can assess refresh optimization on its own merits.

Alternative considered:

- Combine verification rebalancing with incremental refresh optimization. Rejected because it would mix a workflow-policy change with a runtime-contract change and make planning riskier.

## Risks / Trade-offs

- [Risk] Lighter broader-scope verification could miss issues that only appear deep in the larger starter library. -> Mitigation: keep deterministic representative non-core smoke as the default broader safeguard and preserve optional manual `100` soak coverage for deliberate tuning sessions.
- [Risk] Docs and commands may drift if some files still imply `100` or `200` are routine gates. -> Mitigation: update validation baseline, local workflow commands, and product planning docs together in one change.
- [Risk] Removing `200` from routine verification could be misread as proving it is unsupported forever. -> Mitigation: document that this is a current local-first verification decision, not a permanent rejection of wider future scopes.
- [Risk] Narrowing verification posture may tempt unrelated runtime semantics changes in the same implementation pass. -> Mitigation: keep non-goals explicit and treat incremental backfill or broader provider assumptions as follow-up changes.

## Migration Plan

No runtime migration is expected. The implementation should:

1. update tests and markers so the representative broader-than-core lane is the default non-core contract
2. remove or retire the routine `200` validation lane
3. update `just` commands and validation docs to match the lighter verification posture
4. update planning/history docs so current Phase 6 expectations no longer imply full `100` or `200` readiness is routine

Rollback is straightforward: restore the heavier marker/command posture and revert the corresponding docs if the lighter contract proves insufficient.

## Open Questions

None.
