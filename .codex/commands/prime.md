Prime the agent with repository context before planning or implementation.

Optional focus: `@ARGUMENTS`

This command is the repo-local priming wrapper. It should respect the Agentic Coding course mindset, but it must be OpenSpec-aware because this repository uses OpenSpec as its planning system.

When relevant, use the thinking posture from `.codex/skills/openspec-explore/SKILL.md`: investigate deeply, ground in the actual codebase, and do not implement during priming.

Do not write code during `/prime`.

## Goal

Build a concise, evidence-backed understanding of:

- the current repository state
- the source-of-truth docs and constraints
- the current OpenSpec state
- the files and systems most relevant to the user's next task

## Workflow

### 1. Inspect repository state

Run:

```bash
git status --short --branch
git log -10 --oneline
rg --files . | sort
```

Use this to identify:

- active branch
- dirty files
- recent implementation focus
- major directories and current command surface

### 2. Read repository source-of-truth context

Read these first:

- `AGENTS.md`
- `README.md`
- `docs/prd.md`
- `docs/decisions.md`
- `docs/reference-guides/validation-baseline.md`
- `pyproject.toml`
- `app/main.py`
- `app/core/config.py`
- `app/core/database.py`
- `app/core/logging.py`

If `@ARGUMENTS` points to a specific feature, also read the most relevant feature or test files for that area.

### 3. Inspect OpenSpec state

OpenSpec is part of the repo workflow, so always check it during priming.

Run:

```bash
openspec list --json
```

Then:

- read `openspec/config.yaml`
- if `openspec/project.md` exists, read it as legacy context that may still contain useful project details
- if there is one clearly relevant active change, run:

```bash
openspec status --change "<name>" --json
```

and read the existing change artifacts before summarizing

### 4. Identify the validation baseline

Extract the actual repo validation gates and prerequisites:

- linting
- type checking
- unit tests
- integration tests
- local server checks
- Docker and database prerequisites

Be explicit about blockers or prerequisites such as:

- required `.env`
- required `DATABASE_URL`
- PostgreSQL or Docker Compose requirements

### 5. Produce a concise priming report

Return a scannable report with these sections:

#### Project Overview

- what the app does now
- current MVP scope
- primary stack

#### Architecture

- current structure
- important shared systems
- important constraints

#### Workflow State

- branch and repo status
- active OpenSpec changes
- whether OpenSpec context is fully migrated to `openspec/config.yaml` or still split with `openspec/project.md`

#### Validation Baseline

- commands that matter
- prerequisites to get them green
- obvious current risks

#### Next Best Command

Recommend the next command based on the state:

- `/plan <change description>` if the user needs a new or updated OpenSpec change
- `/execute <change-name>` if an OpenSpec change is ready for implementation
- `/openspec-proposal`, `/openspec-apply`, or `/openspec-archive` if the official OpenSpec command is a better fit
- the `openspec-explore` skill if the requirements are still too fuzzy for planning

## Guardrails

- Be repo-specific. Do not give generic priming summaries.
- Prefer evidence from files and commands over assumptions.
- Do not implement or edit files.
- Keep the report concise but useful enough that the next planning or execution step can start immediately.
