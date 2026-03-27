## Context

The repository already exposes the local operator paths needed for market-data smoke validation:

- `just market-refresh-yfinance` / `uv run python -m scripts.data_sync_operations market-refresh-yfinance`
- `just data-sync-local` / `uv run python -m scripts.data_sync_operations data-sync-local`

Recent changes stabilized the operator contract around:

- staged refresh scopes (`core`, `100`, `200`)
- bounded empty-history fallback
- explicit default-currency fallback for missing provider metadata
- typed success evidence and structured blocker evidence

The remaining gap is no longer implementation shape; it is the lack of fresh live evidence after the new recovery contract landed. The current roadmap and backlog explicitly treat refreshed staged smoke evidence as the next gate before wider operational claims or downstream market-data read work.

This proposal intentionally narrows smoke capture to the currently practical staged scopes (`core`, `100`) so evidence can be completed and documented without long-running `200` execution overhead in this cycle.

This change is operator- and documentation-focused. It should avoid new app code unless fresh smoke outcomes prove that the current implementation and the documented operator contract no longer match.

## Goals / Non-Goals

**Goals:**

- Capture fresh standalone refresh evidence for `core` and `100` in a deterministic staged order.
- Capture one fresh combined `data-sync-local` smoke result under the current operator contract.
- Record exact commands, prerequisites, timestamps, and observed outputs in a durable evidence artifact.
- Align operator guides, validation guidance, and product planning docs with the fresh observed posture.
- Record explicit deferral of `200` smoke evidence from this change and keep it as follow-up planning input.
- Preserve fail-fast honesty: blocked outcomes are valid evidence and must not be rewritten as success.

**Non-Goals:**

- Adding a latest-price read boundary or any market-valued analytics.
- Changing provider recovery semantics, request pacing, or refresh-scope behavior unless a new mismatch is proven.
- Implementing incremental extraction, watermark tables, or narrower date-window refresh logic inside this evidence-only change.
- Running `200` smoke in this change.
- Adding scheduler, queue, worker, or public market-data API infrastructure.
- Treating market-data refresh success as permission to mutate ledger or canonical boundaries.

## Decisions

### Decision: Treat this as an evidence-first closeout change

This change exists to capture fresh operational truth after stabilization, not to force another round of adapter/service work. If the staged smoke sequence succeeds, the evidence should prove that. If it blocks, the evidence should document the exact blocker and the resulting readiness posture.

Alternative considered:

- Update code and docs proactively before running smoke. Rejected because it would speculate about live-provider behavior instead of grounding the next decision in fresh evidence.

### Decision: Store fresh smoke outcomes in a dedicated market-data evidence artifact

The refreshed smoke results should live in a dated artifact under `docs/evidence/market-data/` so the operator history is easy to find and does not get buried inside changelog prose alone. The artifact should include:

- environment/prerequisite notes
- exact commands
- invocation timestamps
- selected scope
- either typed success evidence or structured blocker evidence for each run

Alternative considered:

- Record outcomes only in `CHANGELOG.md`. Rejected because changelog entries should stay concise and are a poor home for full operator evidence.

### Decision: Freeze the staged sequence as `core -> 100`, then one combined sync run

The standalone sequence should progress from narrowest to wider practical scope so later outcomes are interpreted in context. One follow-on `data-sync-local` run should then confirm the current combined operator posture without inventing a second readiness contract.

Alternative considered:

- Run combined sync first or skip it entirely. Rejected because the repository already documents `data-sync-local` as part of the current operator surface and validation baseline.

### Decision: Defer `200` smoke from this change

This change will not require running `200`. The proposal focuses on capturing complete, current evidence for `core` and `100`, plus one combined sync run, then documenting `200` as deferred follow-up scope.

Why this over continuing to run `200` in this cycle:

- The immediate goal is to produce concrete, timely readiness evidence for runnable scopes.
- Long `200` runs were blocking progress on evidence closeout and documentation alignment.

Alternative considered:

- Keep `200` as a required step in this change. Rejected because it made this evidence closeout operationally impractical.

### Decision: Preserve existing command surfaces and payload contracts

The execute phase should not redesign the command or payload format. It should use the current output contracts and only document or escalate deviations if the real outputs no longer match the promised evidence fields.

Alternative considered:

- Expand the payload shape or add new command flags in the same change. Rejected because that would turn an evidence closeout into a mixed implementation change.

## Risks / Trade-offs

- [Risk] Live-provider behavior may differ from prior smoke runs. -> Mitigation: record exact timestamps, commands, and raw success/blocker fields instead of summarizing loosely.
- [Risk] Fresh smoke may expose a new contract gap that cannot be solved with docs alone. -> Mitigation: stop at blocker evidence and recommend a dedicated follow-up implementation proposal instead of widening this change.
- [Risk] Narrowing smoke to `core` and `100` leaves `200` unverified in this cycle. -> Mitigation: document `200` as explicit deferred follow-up scope rather than implied readiness.
- [Risk] Combined sync reruns will update market-data rows and counters in expected ways that can be misread as unsafe mutation. -> Mitigation: document that price insert/update churn is expected within the market-data boundary and separate it from ledger/canonical non-mutation guarantees.

## Migration Plan

No runtime migration is expected. This is a documentation/evidence closeout change unless fresh smoke uncovers a new implementation blocker that must be spun into follow-up work. `200` smoke is explicitly deferred from this change.

## Open Questions

None.
