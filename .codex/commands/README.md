# Commands Guide

This folder contains repo-local commands for working effectively in this codebase with Codex.

These commands align with:
- repository rules in `AGENTS.md`
- product and delivery guidance in `docs/`
- the OpenSpec workflow used in this repository

## Recommended Flow

Use this sequence most of the time:

```text
/new-branch <type> <short-description>
/prime
/next-step
/plan <change description>
/review-fix [optional findings]
/explain <change-name> <task-selector>   # optional learning/review step
/execute <change-name> [task-selector]
/self-heal-ci [optional target/using]
/validate
/commit-local [optional intent]
/commit [optional intent]
```

Mental model:
- `/new-branch` = start from synced `main`, create branch with standard naming, configure upstream, and optionally publish
- `/prime` = understand current repo and OpenSpec runtime
- `/next-step` = pick the highest-leverage next implementation step
- `/plan` = produce an execution-ready plan from OpenSpec artifacts
- `/review-fix` = convert review findings into a minimal fix plan in `/explain` structure
- `/explain` = explain task slices before coding (read-only)
- `/execute` = implement task slices with explicit validation
- `/self-heal-ci` = iterate minimal fixes until local CI gates converge or a real blocker is confirmed (`target=fast|full`, `using=back|front|all`)
- `/validate` = report what actually passes, fails, or is blocked
- `/commit-local` = create a local commit and stop before push
- `/commit` = package verified work into clean commits

## OpenSpec Relationship

This repo uses OpenSpec as planning and change-management source of truth.

That means:
- planning artifacts live under `openspec/changes/<change>/`
- execution should run from OpenSpec apply instructions
- validation should account for whether scope is repo-wide or change-specific

You can also use official OpenSpec skills directly when better fit:
- `$openspec-propose`
- `$openspec-apply-change`
- `$openspec-archive-change`
- `$openspec-explore`

## Commands

### `/prime`

Use when:
- starting a new session
- returning after context loss
- before planning or implementation

What it does:
- checks repo state and constraints
- checks OpenSpec runtime state (`status` + `apply`)
- reports alignment risks/blockers
- recommends one best next command

Examples:

```text
/prime
/prime scope=docs mode=quick
/prime change=add-pdf-ingestion-without-persistence
```

### `/new-branch`

Use when:
- starting a new change in repos where `main` is PR-only
- you want a single branch-start command that syncs + creates + configures upstream without mandatory push
- you may need to carry a dirty tree into the new branch intentionally (`working_tree=pass`)

What it does:
- verifies you are on local `main` and enforces selected dirty-tree policy
- runs `git fetch origin --prune` + optional `git pull --ff-only origin main` depending on dirty-tree mode
- creates branch with format `<type>/<short-slug>-YYYYMMDD`
- validates ref name and collisions
- configures upstream/tracking for `origin/<same-branch-name>`
- optional publish only when `push=on`
- supports dirty tree modes:
  - `working_tree=pass` (default; carry local dirty tree to new branch)
  - `working_tree=block`
  - `working_tree=stash` (stash, sync, create, pop)

Examples:

```text
/new-branch feat market-data-sync-ops
/new-branch docs yfinance-refresh-runbook
/new-branch type=fix name=adapter-single-column-mismatch
/new-branch fix slug=auto working_tree=pass
```

Compatibility note:
- `/branch` remains as deprecated alias pointing to `/new-branch`.

### `/next-step`

Use when:
- deciding what to build next
- needing a scored recommendation grounded in docs + code

What it does:
- evaluates candidate next steps
- scores top options
- recommends one winner and exact next command

Examples:

```text
/next-step
/next-step pdf pipeline
```

### `/plan`

Use when:
- turning an active OpenSpec change into execution-ready implementation planning
- reviewing readiness and quality before coding

What it does:
- reads OpenSpec `status` and `instructions apply`
- runs task quality gate (`Pass | Advisory Gap | Fail`)
- checks design open questions before phased planning
- requires explicit blind-spot analysis and blast-radius diagnosis
- outputs phased execution plan + validation matrix

Examples:

```text
/plan
/plan add-pdf-ingestion-without-persistence
```

### `/explain`

Use when:
- you want task-level implementation understanding before coding
- you want a minimality review for a selected task slice

What it does:
- explains selected task(s) with architecture-aware rationale
- distinguishes planned vs implemented behavior
- can include representative code-shape diffs without editing files

Examples:

```text
/explain add-pdf-ingestion-without-persistence 2.1
/explain openspec/changes/add-pdf-ingestion-without-persistence/tasks.md 2.1-2.3 depth=deep
```

### `/review-fix`

Use when:
- you just ran `/review` and need a minimal, actionable fix plan
- you want `/explain`-structured diagnosis before coding

What it does:
- resolves findings from the latest built-in code-review action context (or explicit input)
- diagnoses root causes and impact per finding
- proposes smallest safe changes aligned with repo rules
- includes rabbit-hole check plus diff/blind-spot analysis

Examples:

```text
/review-fix
/review-fix <paste findings block>
/review-fix <paste findings block> depth=deep
```

### `/execute`

Use when:
- an OpenSpec change is implementation-ready
- you want task-by-task execution with selectors

What it does:
- resolves change or direct `tasks.md` path
- supports selectors like `1.1`, `1.1-1.3`, `2.*`
- supports `preflight=auto|off`
- runs task-local proof first, broader checks on change completion

Examples:

```text
/execute add-pdf-ingestion-without-persistence
/execute add-pdf-ingestion-without-persistence 2.1-2.2
/execute openspec/changes/add-pdf-ingestion-without-persistence/tasks.md 3.* preflight=off
```

### `/self-heal-ci`

Use when:
- local `just ci-fast` or `just ci` is red and you want iterative auto-repair
- you want one command to converge failing gates before commit/push

What it does:
- runs selected CI target (`target=fast|full`) on selected scope (`using=back|front|all`, default `all`)
- isolates first failing gate
- applies minimal fix
- reruns iteratively up to a max cycle count
- exits as `PASS`, `PARTIAL PASS`, `BLOCKED`, or `FAIL` with concrete next action

Examples:

```text
/self-heal-ci
/self-heal-ci target=fast
/self-heal-ci target=full using=back max=5 autofix=on
```

### `/validate`

Use when:
- you want baseline validation for repo or active change
- you need clear `PASS | PARTIAL PASS | FAIL | BLOCKED`

What it does:
- establishes validation scope first
- runs only justified checks from the baseline toolchain (`ruff`, `black`, `bandit`, `pyright`, `mypy`, `ty`, `pytest`)
- reports passed/failed/blocked/skipped with evidence

Examples:

```text
/validate
/validate add-pdf-ingestion-without-persistence
```

### `/commit`

Use when:
- you have completed and validated coherent work
- you want clean commit grouping and safe push flow

What it does:
- inspects real diff
- stages intended atomic file groups
- proposes descriptive conventional commit message
- asks for approval before commit(s) and push

Examples:

```text
/commit
/commit add pdf ingestion docs
```

### `/commit-local`

Use when:
- you want one single local commit but will push manually later
- you want the command to stage the full working tree and stop after commit creation

What it does:
- inspects staged, unstaged, and untracked changes together
- stages the intended full local change with `git add -A`
- proposes a descriptive conventional commit message
- creates the local commit and stops before push

Examples:

```text
/commit-local
/commit-local finalize docs reorganization
```

### `/check-ingore-comments`

Use when:
- auditing `noqa`, `type: ignore`, or `pyright: ignore` usage

What it does:
- finds suppressions
- explains why they exist
- recommends keep/remove/refactor

Note:
- filename currently uses `ingore` instead of `ignore`

## Best Practices

- Run `/prime` before non-trivial planning/execution.
- Use `/next-step` when direction is unclear.
- Use `/plan` before `/execute` for non-trivial changes.
- Use `/explain` when you want to review a slice before coding it.
- Keep `/execute` runs task-scoped and validation-backed.
- Use `/validate` for reality-based status, not optimistic status.
- Use `/commit-local` when the commit should be created now but pushing will be manual.
- Use `/commit` only after validations are acceptable for scope.

## Notes

- Keep command docs aligned with real repo structure and workflow.
- If command behavior changes, update this README in the same change.
