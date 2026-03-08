Create or refine an implementation plan using OpenSpec as the primary planning system.

Input: `@ARGUMENTS`

This command is the repo-local planning wrapper around OpenSpec. It should follow the Agentic Coding course's planning discipline, but the canonical planning artifacts for this repository should live in `openspec/changes/<change>/`.

Use `.codex/skills/openspec-propose/SKILL.md` as the underlying OpenSpec behavior reference for artifact generation. This command is the repo-specific wrapper around that workflow.

Do not create ad hoc plan files unless the user explicitly asks for them.

## Goal

Turn the user's request into an implementation-ready OpenSpec change with the right artifacts, scope boundaries, and executable tasks.

## OpenSpec-first rule

For Codex, OpenSpec officially supports proposal and apply workflows through commands and skills. This local `/plan` command should behave like a course-style planning command, but it must use the OpenSpec workflow under the hood.

If the request is purely "make me an OpenSpec proposal", `/openspec-proposal` is the direct official path.

If the user asks for `/plan`, do the same work through this repo-local command so the workflow stays consistent with the rest of the command layer.

## Workflow

### 1. Understand the request

If `@ARGUMENTS` is missing or too vague, ask the user what change they want to build.

Derive:

- a short plain-English scope statement
- a kebab-case OpenSpec change name

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

Otherwise create one:

```bash
openspec new change "<name>"
```

### 4. Build artifacts the OpenSpec way

Use the OpenSpec CLI to determine artifact order and requirements:

```bash
openspec status --change "<name>" --json
```

For each artifact that is ready:

```bash
openspec instructions <artifact-id> --change "<name>" --json
```

Read dependency artifacts before writing the next artifact.

Create or update the artifacts until the change is ready for implementation.

Follow the same artifact discipline as the local OpenSpec propose skill:

- proposal explains what and why
- design explains how
- tasks are concrete and execution-ready

The usual target is:

- `proposal.md`
- `design.md`
- `tasks.md`

but always follow what the schema actually requires.

### 5. Apply repository planning standards

While generating artifacts, make sure the plan follows this repo's actual rules:

- stay inside current MVP scope unless the user explicitly expands it
- keep changes minimal and auditable
- preserve ledger-first and contract-first thinking
- prefer vertical-slice boundaries over cross-cutting sprawl
- keep transaction ledger, market data, and derived analytics separate
- require deterministic validation for extraction and persistence work
- preserve strict typing, structured logging, and Docker-first local development

### 6. Make tasks execution-ready

Every task should be:

- atomic
- ordered
- scoped to concrete files or systems
- tied to a validation step

Prefer tasks that tell the executor:

- what file or area to touch
- what pattern to mirror
- what gotcha to avoid
- how to validate completion

If a design or scope question is unresolved, capture it explicitly instead of hiding it in assumptions.

### 7. Report readiness

After artifact generation, report:

- change name
- change path
- artifacts created or updated
- major scope decisions
- unresolved questions or risks
- whether the change is ready for `/execute <change-name>` or `/openspec-apply`

## Guardrails

- OpenSpec artifacts are the planning source of truth.
- Do not skip reading repository docs before planning.
- Do not create duplicate active changes for the same work.
- Do not push vague tasks downstream. If something is unclear, capture it as a decision, note, or explicit follow-up.
- Keep the plan aligned with current repo scope and architecture rather than external repo patterns.
