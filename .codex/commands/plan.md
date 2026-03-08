Create or refine an implementation plan using OpenSpec as the primary planning system.

Input: `@ARGUMENTS`

This command is the repo-local planning wrapper around OpenSpec. The canonical planning artifacts for this repository must live in `openspec/changes/<change>/`.

This command is intentionally approval-gated. It must not fast-forward through all artifacts in one turn unless the user explicitly asks for that behavior.

Do not create ad hoc plan files unless the user explicitly asks for them.

## Goal

Turn the user's request into an OpenSpec change that is:
- minimal
- surgical
- aligned with this repo's rules
- reviewed by the user artifact by artifact before implementation

## OpenSpec-first rule

Use OpenSpec artifacts as the planning source of truth.

This local `/plan` command is not the fast-forward proposal path. It should support a collaborative planning loop where the user participates in each artifact before continuing.

If the user explicitly wants a one-shot proposal, they should use the official OpenSpec fast-forward workflow instead.

## Planning stance

Default to an investigative planning pass first.

That means:
- inspect the repo and docs
- clarify scope
- identify likely capabilities and risks
- surface open questions early
- avoid writing artifacts until the request is understood well enough

Do not rush into artifact creation just because a change name can be derived.

## Workflow

### 1. Investigate the request first

If `@ARGUMENTS` is missing or too vague, ask the user what change they want to build.

Derive:
- a short plain-English scope statement
- a proposed kebab-case OpenSpec change name
- likely capability names
- likely open questions
- whether the request is narrow enough for a minimal, surgical implementation

Before writing anything, tell the user:
- your interpretation of the scope
- the proposed change name
- the likely artifact sequence
- the first open questions that could affect planning quality

If the scope is still unclear, stop and resolve that first.

### 2. Prime relevant context before planning

Read the planning context before creating or updating artifacts:

- `AGENTS.md`
- `README.md`
- `docs/prd.md`
- `docs/decisions.md`
- `docs/references.md`
- `docs/reference-guides/validation-baseline.md`
- `openspec/config.yaml`
- `openspec/project.md` if it exists

Also inspect the current repository state:

```bash
git status --short --branch
openspec list --json
```

### 3. Resolve whether the change already exists

If an active OpenSpec change already matches the requested work:
- continue that change
- do not create a duplicate
- tell the user you are continuing it

Otherwise create one:

```bash
openspec new change "<name>"
```

After creating or selecting the change, tell the user:
- change name
- change path
- whether this is a new change or an existing one

### 4. Build artifacts one at a time

Use the OpenSpec CLI to determine artifact order and requirements:

```bash
openspec status --change "<name>" --json
```

For the next ready artifact only:

```bash
openspec instructions <artifact-id> --change "<name>" --json
```

Read dependency artifacts before writing the next artifact.

Default artifact order for `spec-driven` work:
1. `proposal`
2. `specs`
3. `design`
4. `tasks`

If the schema or CLI output requires a different order, follow the schema.

Do not create more than one artifact in the same approval cycle unless the user explicitly asks to continue without review.

### 5. Pause after each artifact

After creating or updating a single artifact:

- summarize what was added or changed
- list open questions, risks, and decisions made
- state whether the next artifact is now unlocked
- stop and ask the user whether to:
  - approve and continue
  - revise this artifact
  - stop here

Do not continue automatically to the next artifact.

If the artifact introduces unresolved questions that materially affect downstream artifacts, stop and resolve them before proceeding.

### 6. Apply repository planning standards

While generating artifacts, make sure the plan follows this repo's rules:

- stay inside current MVP scope unless the user explicitly expands it
- keep implementations minimal, surgical, and auditable
- preserve ledger-first and contract-first thinking
- prefer vertical-slice boundaries over cross-cutting sprawl
- keep transaction ledger, market data, and derived analytics separate
- require deterministic validation for extraction and persistence work
- preserve strict typing, structured logging, and the repo's conventions
- do not introduce new dependencies, config, routes, or storage behavior unless necessary

For every proposed implementation:
- justify why it is necessary
- prefer the smallest viable design
- avoid speculative abstractions

### 7. Make tasks execution-ready and history-friendly

When creating `tasks.md`:

- tasks must remain checkbox-based and parser-safe
- keep tasks atomic, ordered, and scoped to concrete files or systems
- tie each task to a validation step
- prefer tasks that tell the executor:
  - what file or area to touch
  - what pattern to mirror
  - what gotcha to avoid
  - how to validate completion

In addition, add `Notes` sections that are useful for both humans and AI agents.

Notes should:
- add context not obvious from the task description
- explain why a task exists
- record constraints, assumptions, or design rationale
- help reconstruct the history of the change later

Do not put notes inside checkbox lines.
Keep notes adjacent to tasks, for example:

```md
## 1. Configuration

- [ ] 1.1 Add settings ...
- [ ] 1.2 Define schemas ...

### Notes
- `1.1`: Keep defaults conservative and configurable.
- `1.2`: Reuse nested preflight output and avoid absolute storage paths.
```

### 8. Report readiness honestly

Only say the change is ready for implementation when:
- all required artifacts are complete
- the user has approved the final planning artifact
- known open questions are either resolved or intentionally deferred in writing

At the end of each `/plan` step, report:
- change name
- change path
- artifact created or updated this step
- major decisions made
- open questions or risks
- whether the next artifact is ready
- whether the change is ready for `/execute <change-name>`

## Guardrails

- OpenSpec artifacts are the planning source of truth.
- Do not skip reading repository docs before planning.
- Do not create duplicate active changes for the same work.
- Do not fast-forward through all artifacts unless the user explicitly asks.
- Do not push vague tasks downstream.
- If something is unclear, capture it as a decision, note, or explicit follow-up.
- Prefer an investigative pass before artifact generation.
- Keep all planning aligned with current repo scope and architecture.
- Keep every implementation proposal minimal and surgical by default.
