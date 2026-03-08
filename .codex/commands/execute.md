Implement an OpenSpec change using the repo's execution and validation standards.

Input: `@ARGUMENTS`

This command is the repo-local execution wrapper around the OpenSpec apply workflow. It should follow the Agentic Coding course's implementation discipline, but it must execute from OpenSpec change artifacts rather than from an ad hoc standalone plan.

Use `.codex/skills/openspec-apply-change/SKILL.md` as the underlying OpenSpec behavior reference for change selection, apply instructions, task progression, and pause conditions. This command adds repo-specific implementation and validation discipline on top.

## Goal

Implement the selected change task by task, validate as you go, and report honestly on what passed, what failed, and what is blocked.

## OpenSpec-first rule

Prefer OpenSpec changes as the execution source of truth.

If the user has not created a change yet:

- do not start freelancing implementation
- tell them to use `/plan <change description>` or `/openspec-proposal`

If the user only wants the official OpenSpec execution path, `/openspec-apply` is the direct command. This local `/execute` command should follow the same underlying workflow while adding repo-specific execution and validation discipline.

## Workflow

### 1. Resolve the target change

If `@ARGUMENTS` includes a change name, use it.

Otherwise:

- inspect active changes:

```bash
openspec list --json
```

- if there is exactly one relevant active change, use it
- if multiple active changes could match, ask the user which one to execute

Always state which change is being used.

### 2. Load the change state

Run:

```bash
openspec status --change "<name>" --json
openspec instructions apply --change "<name>" --json
```

Use this to determine:

- the schema in use
- the current progress
- the context files that must be read
- the remaining tasks
- whether execution is blocked because artifacts are incomplete

If the change is not implementation-ready, stop and explain what artifact is missing.

### 3. Read context before coding

Read every file listed in the OpenSpec apply instructions.

Also read the repo-level execution context that should always shape implementation:

- `AGENTS.md`
- `README.md`
- `docs/reference-guides/validation-baseline.md`
- any repo files directly referenced by the change artifacts

Before editing, restate:

- current task progress
- implementation order
- validation expectations
- any known environment prerequisites

### 4. Implement one task at a time

Work in task order unless the artifacts clearly justify a different order.

For each task:

- make the smallest coherent change that completes it
- mirror existing repo patterns before inventing new ones
- preserve strict typing and structured logging conventions
- stay inside the task scope

If implementation reveals a design flaw or scope mismatch:

- stop
- explain the issue
- propose updating the OpenSpec artifacts before continuing

### 5. Validate continuously

Do not defer validation until the very end.

After each meaningful task, run the smallest validation that proves the task works.

At the end, run the repo baseline that applies to the change:

```bash
uv run ruff check .
uv run pyright app/
uv run mypy app/
uv run pytest -v
```

If the change touches database or integration behavior, also run the relevant environment setup and integration checks:

```bash
docker-compose up -d db
uv run alembic upgrade head
uv run pytest -v -m integration
```

If a required service is not available, say so explicitly and report what could and could not be validated.

### 6. Update task status honestly

Only mark a task complete after:

- the code change is done
- the relevant validation for that task passed, or the remaining blocker is explicitly reported

Update task checkboxes in the OpenSpec task artifact as progress is made.

### 7. Report with evidence

At the end, report:

- change name
- tasks completed this session
- files added and modified
- validations run
- pass/fail status for each validation
- blockers, risks, or follow-up changes needed

If all tasks are complete, say the change is ready for `/openspec-archive` or the archive skill.

## Guardrails

- Do not implement without an OpenSpec change unless the user explicitly overrides that workflow.
- Do not skip reading the apply context.
- Do not claim validations passed if they did not run.
- Do not silently work around design problems. Surface them and push them back into the change artifacts when needed.
- Keep changes task-scoped, reviewable, and compatible with the repo's Docker-first validation flow.
