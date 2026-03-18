Build a repository-fit OpenSpec implementation plan before coding.

Input: `@ARGUMENTS` (optional change name)

This command is planning-only. It must not implement production code.

## Objective

Convert approved OpenSpec artifacts into a low-risk implementation plan that respects:
- test-first discipline
- investigation before implementation
- task-level traceability using concise notes
- fail-fast behavior
- architecture boundaries in this repo
- documentation and validation obligations

## Input

Optional argument:
- `<change-name>`

If no argument is provided:
- run `openspec list --json`
- if only one clearly relevant active change exists, use it
- if multiple active changes are plausible, ask the user to choose

## Guardrails

- Do not modify application code during planning.
- Do not modify OpenSpec artifacts unless the user explicitly asks.
- Use OpenSpec CLI JSON output as source of truth.
- Prefer minimal, incremental work over broad refactors.
- Follow repository architecture and typing rules from `AGENTS.md`.
- Call out fail-fast requirements when external dependencies/config are in scope.
- Include relevant docs and validation obligations explicitly.
- Treat unresolved `Open Questions` in `design.md` as planning-critical inputs.

## Task Quality Gate

Evaluate task quality with:
- `Pass`
- `Advisory Gap`
- `Fail`

Checks:
1. Investigation-first structure
- `Pass`: explicit investigation section or equivalent early discovery task
- `Advisory Gap`: no explicit section, but plan is still low-risk
- `Fail`: missing investigation and meaningful unknowns remain
2. Notes on tasks
- `Pass`: tasks include concise, useful notes where needed
- `Advisory Gap`: notes are sparse but plan remains executable
- `Fail`: intent or constraints are ambiguous without notes
3. Test-first intent
- tasks begin with failing or baseline-locking tests when behavior changes
4. Scope discipline
- tasks are grouped into coherent units (`app`, `docs`, `verification`, `infra` as needed)
5. Documentation coverage
- changed behavior/contracts include docs updates where needed
6. Verification coverage
- explicit validation tasks and evidence expectations exist
7. Architecture/governance fit
- artifacts align with strict typing, logging conventions, and repository structure

If any gate is `Fail`:
- stop planning
- output `Task Refinement Needed`
- list minimum artifact edits required before safe execution

If any gate is `Advisory Gap`:
- planning may continue
- recommend minimum refinements before `/execute`

## Process

### 1) Select the Target Change

Run:

```bash
openspec list --json
```

### 2) Confirm Workflow State

Run:

```bash
openspec status --change "<change-name>" --json
openspec instructions apply --change "<change-name>" --json
```

Use:
- `status` for artifact readiness
- `apply` for implementation progress and pending task inventory

If `apply.state` is `blocked`, stop and recommend completing artifacts first.

### 3) Load Planning Context

Read:
- files from `contextFiles` in `openspec instructions apply`
- `AGENTS.md`
- `README.md`
- `openspec/config.yaml`
- `docs/reference-guides/validation-baseline.md`
- relevant domain docs (`docs/prd.md`, `docs/decisions.md`) when needed

### 4) Review Design Open Questions

Inspect `design.md` for an `Open Questions` section.

Rules:
- if `design.md` is absent: `Open Questions Review: Pass (no design.md)`
- if section absent: `Open Questions Review: Pass (none listed)`
- if section says none/closed: `Open Questions Review: Pass`
- if unresolved questions exist: `Open Questions Review: Decision Needed`

When unresolved questions exist:
- stop before phased planning
- list one bullet per question with:
  - `Why:`
  - `Affects:`
  - `Recommendation:`
- end with `Planning Paused Pending Design Decisions`

### 5) Run the Task Quality Gate

Apply the quality checks above.

If any gate is `Fail`, stop.

### 6) Build Task Decomposition

Decompose into work units, for example:
- `app`
- `shared`
- `docs`
- `infra`
- `verification`

For each unit identify:
- dependencies
- likely files/modules touched
- risk level: `Low` | `Medium` | `High`

### 7) Build Validation Matrix

Choose smallest commands that still meet repository expectations.

Typical commands:
- OpenSpec/docs:
  - `openspec validate --specs --all`
- App code:
  - `uv run ruff check .`
  - `uv run pyright app/`
  - `uv run mypy app/`
  - targeted `uv run pytest -v <path-or-node>`
- Integration/db only when needed:
  - `docker-compose up -d db`
  - `uv run alembic upgrade head`
  - `uv run pytest -v -m integration`

### 8) Build the Phased Plan

For each phase include:
- goal
- tasks covered
- likely touched areas
- risks and mitigations
- exact validation commands
- exit criteria

### 9) Recommend Best Next Action

Usually:
- `/execute <change-name> <first-task-or-bundle>`

Fallbacks:
- `/explain <change-name> <task-selector>` for walkthrough-first
- `$openspec-apply-change` as implementation skill fallback

## Output Format

### 1) Change Snapshot
- change name
- schema
- apply state
- progress
- implementation readiness

### 2) Design Open Questions Review
- Status: `Pass` | `Decision Needed`
- if `Decision Needed`: list question bullets (`Why`, `Affects`, `Recommendation`) and stop

### 3) Task Quality Gate
- Investigation-first structure: `Pass` | `Advisory Gap` | `Fail`
- Notes on tasks: `Pass` | `Advisory Gap` | `Fail`
- Test-first intent: `Pass` | `Advisory Gap` | `Fail`
- Documentation coverage: `Pass` | `Advisory Gap` | `Fail`
- Verification coverage: `Pass` | `Advisory Gap` | `Fail`
- Architecture/governance fit: `Pass` | `Advisory Gap` | `Fail`

### 4) Task Decomposition
- ordered work units
- dependencies
- risk level per unit

### 5) Phased Plan
- one phase at a time with goal, touched areas, validations, exit criteria

### 6) Validation Matrix
- exact commands
- when to run them
- expected evidence

### 7) Documentation Checklist
- docs to update for changed behavior/contracts
- spec/delta alignment checks as relevant

### 8) Recommended Next Command
- one exact next command
- one fallback command

### 9) Confidence
- `High` | `Medium` | `Low`
- short reason

### 10) Open Questions
- only blockers requiring user input

## Definition of Done

Planning is complete when:
- one target change is selected
- artifact readiness and apply progress were both checked
- design open questions were reviewed before phased planning
- unresolved design questions pause planning
- quality gate status is explicit
- phased execution + validation are explicit
- one clear next command is recommended
