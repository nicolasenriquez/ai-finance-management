## Context

`phase-k` closes transparency and governance gaps for DCA controls in the current copilot flow. The next step is productizing a personal DCA chat assistant after:

- `phase-k-dca-controls-and-governance-closeout` implementation is complete
- `archive-v0-and-build-compact-trading-dashboard` reaches a stable copilot integration surface

The provided DCA tutorial defines a stable behavior philosophy:

- stay consistent with baseline periodic investing
- increase allocation on qualified dips, not emotional swings
- require fundamentals confidence before aggressive adds
- avoid overinvesting and preserve financial resilience
- review and adjust with life/cashflow changes

To make this operational, we need an architecture where deterministic policy checks are the source of truth and AI narration only interprets those checks.

Constraints:

- Keep copilot read-only and non-executing.
- Keep non-advice posture explicit.
- Preserve strict typed contracts and fail-fast validation.
- Reuse existing workspace launcher model (docked + expanded) where possible.
- Avoid front-end contract churn while dashboard IA/workspace replacement is still unstable.

## Goals / Non-Goals

**Goals:**

- Formalize one DCA SOT policy contract for personal assessments and recommendations.
- Add deterministic calculator tools for DCA planning and KPI comparison.
- Add typed personal policy context inputs so guidance can be personalized without hidden assumptions.
- Add deterministic context-card synthesis (gainers/losers/news summary) to ground personal DCA conversations.
- Add explicit tool/lifecycle streaming semantics and bounded conversation persistence for continuity.
- Keep evidence and tool-trace transparency explicit in the assistant UX.
- Keep recommendations bounded by deterministic rules plus caveated interpretation.

**Non-Goals:**

- Trade execution, order routing, or portfolio mutation.
- Guaranteed-return, target-price, or timing-certainty claims.
- Free-form SQL or unrestricted data access for assistant workflows.
- Persistent autonomous agent loops.
- Unbounded chat memory or opaque retention policies.

## Decisions

### Decision: Use a deterministic-first DCA policy engine as SOT

The assistant will evaluate DCA assessments in this order:

1. Eligibility and data sufficiency gates
2. DCA baseline cadence checks
3. Double-down threshold checks with 52-week gating
4. Fundamentals proxy checks and caveats
5. Concentration/risk impact checks
6. Monitoring and review cadence output

Rationale:

- Prevents policy drift between UI, prompt language, and backend behavior.
- Keeps recommendations inspectable and testable.

Alternatives considered:

- Prompt-only policy interpretation: rejected due to inconsistency and lower auditability.

### Decision: Add typed personal policy context with explicit insufficiency semantics

Request contracts will include optional but typed policy context fields (for example: monthly DCA budget, concentration cap, emergency-fund months, debt-stress flag, review cadence).

If required fields for a requested assessment are missing, responses must return explicit insufficiency caveats instead of inferred personal assumptions.

Rationale:

- Supports personalization without violating fail-fast principles.
- Avoids hidden assumptions that look like advice.

### Decision: Introduce `dca_assessment` as a first-class operation

`dca_assessment` will be a dedicated operation for personal DCA guidance, while `chat` and `opportunity_scan` remain available.

Rationale:

- Separates general portfolio Q&A from policy-driven DCA assessments.
- Simplifies frontend mode-specific controls and test contracts.

### Decision: Provide deterministic DCA calculator toolpack

The assistant will expose deterministic calculator outputs for:

- baseline vs 2x DCA scenario comparison
- projected average cost basis impact
- concentration delta after planned contributions
- threshold-monitor state for currently held symbols

Rationale:

- Enables practical planning actions beyond narrative text.
- Reduces reliance on opaque model calculations.

### Decision: Add deterministic portfolio context cards before narration

Each `dca_assessment` response will include one bounded context-card bundle:

- top gainers/losers snapshot from held symbols
- concentration and weight deltas tied to planned DCA additions
- short symbol-relevant news summary with explicit source/evidence caveats

Rationale:

- Improves conversational grounding for "why today?" and "why this symbol?" queries.
- Reuses existing portfolio/news context capabilities instead of prompting blind narration.

Alternatives considered:

- Narration-only contextual framing: rejected due to higher hallucination and lower auditability risk.

### Decision: Keep docked + expanded assistant UX with event transparency

Assistant UI keeps:

- desktop docked panel and mobile full-screen model
- expanded route for deep review
- explicit lifecycle and tool-event timeline semantics (`start`, `token`, `tool_call`, `end`, `error`)

Rationale:

- Preserves existing workspace continuity.
- Aligns with proven full-stack agent UI patterns where users inspect generation and tool phases for trust (reference: `https://github.com/vstorm-co/full-stack-ai-agent-template` and `https://github.com/vstorm-co/full-stack-ai-agent-template/blob/main/docs/ai-agent.md`).

### Decision: Add bounded conversation persistence with evidence-linked replay

Assistant sessions will persist bounded message history and evidence pointers for longitudinal DCA analysis, with strict retention bounds and explicit user-visible session context.

Rationale:

- Personal DCA workflows are longitudinal; pure ephemeral chat undermines consistency.
- Evidence-linked replay supports auditability for why recommendations changed over time.

Alternatives considered:

- Session-local memory only: rejected for weak continuity.
- Unbounded persistent memory: rejected for governance and privacy risk.

### Decision: Introduce copilot observability baseline for assistant workflows

The assistant should emit traceable telemetry for:

- request lifecycle state transitions
- tool invocation metadata
- response latency and error class
- model/token usage where available

Rationale:

- Needed for reliability, regression triage, and governance evidence.
- Matches production agent patterns with explicit AI-operation observability.

### Decision: Keep this change downstream of phase-k and dashboard stabilization

Implementation for this change starts only after:

- phase-k request/response contracts and DCA-control surfaces are delivered
- dashboard rebuild change stabilizes the target copilot container/shell

Rationale:

- Prevents rework from concurrent contract and layout churn.
- Keeps execution aligned with `/plan` guidance to continue highest-leverage active work first.

## Risks / Trade-offs

- [Policy overreach without personal finance data] -> Require explicit insufficiency handling and caveats.
- [Calculator overload in compact assistant UI] -> Use progressive disclosure (`chat`, `calculators`, `policy` modules).
- [Users misread assessments as advice] -> Keep fixed non-advice language and deterministic evidence trace.
- [Contract complexity growth] -> Keep strict bounds, typed defaults, and fail-first tests for each new field.
- [Post-dashboard sequencing risk] -> Keep this change dependent on `archive-v0` completion for UI integration timing.
- [Persistence introduces privacy/compliance risk] -> Bound retention, expose session controls, and keep read-only data posture.
- [Streaming/tool-event UX drift] -> Freeze event contract and add frontend snapshot tests for timeline rendering.
- [Concurrent change overlap with phase-k] -> Gate phase-o execution until phase-k is validated and merged to avoid duplicated edits.

## Migration Plan

1. Confirm dependency gates: `phase-k` complete plus dashboard copilot surface stable.
2. Add fail-first tests for new request/response contracts (`dca_assessment`, policy context, calculator outputs, event stream, session persistence).
3. Implement deterministic DCA policy engine extensions, calculator toolpack, and context-card synthesis in backend.
4. Wire frontend composer mode, policy inputs, calculator/context-card surfaces, and event-aware timeline.
5. Implement bounded session persistence and evidence-linked replay semantics.
6. Add observability instrumentation and validation for assistant lifecycle/tool usage.
7. Run backend/frontend validation gates and document SOT governance behavior.
8. Update changelog and OpenSpec validation artifacts for handoff.

Rollback:

- Disable `dca_assessment` operation while keeping existing `chat` and `opportunity_scan` intact.
- Keep calculator outputs feature-flagged so core chat remains available.
- Disable persistence/event-stream enhancements behind feature gates if operational risk appears.

## Open Questions

- Should personal policy context remain session-local in v1 of this phase, or be persisted per user profile?
- Should calculator outputs be response-inline only, or also stored as journal snapshots for later comparison?
