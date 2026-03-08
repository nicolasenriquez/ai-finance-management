# Commands Guide

This folder contains repo-local commands for working effectively in this codebase with Codex.

These commands are designed to follow:

- the repository rules in `AGENTS.md`
- the MVP and delivery guidance in `docs/`
- the OpenSpec workflow used in this repository

The commands are not random shortcuts. Together they form a practical workflow for:

- understanding the repo
- choosing the right next step
- planning work with OpenSpec
- executing changes safely
- validating the result honestly

## Recommended Flow

Use the commands in this order most of the time:

```text
/prime
/next-step
/plan <change description>
/execute <change-name>
/validate
/commit [optional intent]
```

Mental model:

- `/prime` = understand the repo
- `/next-step` = choose the best next implementation step
- `/plan` = investigate, then create or refine the OpenSpec change artifact by artifact
- `/execute` = implement the change task by task
- `/validate` = prove what actually works now
- `/commit` = package verified work and push it to `origin main`

## OpenSpec Relationship

This repo uses OpenSpec as the planning and change-management system.

That means:

- planning artifacts should live under `openspec/changes/<change>/`
- execution should preferably happen from an OpenSpec change
- validation should understand whether it is validating the whole repo or a specific change

You can also use the official OpenSpec commands and skills directly when that is a better fit:

- `/openspec-proposal`
- `/openspec-apply`
- `/openspec-archive`

Repo-local commands exist to make the workflow more natural for this codebase and to add repo-specific rules on top of OpenSpec.

## Commands

### `/prime`

Use when:

- starting a new session
- returning after context loss
- before planning anything non-trivial
- before asking for a codebase review or architecture diagnosis

What it does:

- reads repo state
- reads the source-of-truth docs
- checks OpenSpec state
- identifies validation prerequisites
- recommends the next best command

Examples:

```text
/prime
/prime pdf extraction pipeline
/prime validation baseline
/prime openspec workflow state
```

### `/next-step`

Use when:

- you want help deciding what to build next
- you want a localized next feature for testing the command workflow
- you want a scored recommendation from the roadmap and current codebase reality

What it does:

- reviews roadmap, backlog, PRD, and codebase state
- proposes top candidate next steps
- scores them
- recommends one winner
- ends with the exact next command to run

Examples:

```text
/next-step
/next-step pdf pipeline
/next-step validation
```

### `/plan`

Use when:

- you know what change you want to build
- you want to create or refine an OpenSpec change
- you want proposal/design/tasks before implementation

What it does:

- reads repo guidance first
- starts with an investigative pass before writing artifacts
- uses OpenSpec as the planning source of truth
- creates or updates the relevant change in `openspec/changes/`
- works artifact by artifact instead of fast-forwarding by default
- pauses for user approval between artifacts
- ensures tasks are concrete, execution-ready, and can include adjacent planning notes without breaking checkbox parsing

Examples:

```text
/plan add pdf preflight analysis
/plan implement canonical transaction normalizer
```

### `/execute`

Use when:

- an OpenSpec change is ready for implementation
- you want to implement task by task from `proposal`, `design`, and `tasks`

What it does:

- reads OpenSpec apply instructions
- loads task context
- implements in order
- validates continuously
- reports blockers honestly

Examples:

```text
/execute add-pdf-preflight-analysis
/execute
```

If no change is specified, the command should infer it only when that is unambiguous.

### `/validate`

Use when:

- you want to validate the current repo state
- you want to validate the current or targeted OpenSpec change
- you want a clear PASS / FAIL / BLOCKED result with next action

What it does:

- determines validation scope first
- runs the relevant repo baseline
- includes environment-dependent checks when needed
- distinguishes passed, failed, blocked, and skipped checks
- recommends the next action

Examples:

```text
/validate
/validate add-pdf-preflight-analysis
/validate validation baseline
```

### `/commit`

Use when:

- you have completed and validated a coherent unit of work
- you want help creating a clean commit and pushing it to `origin main`

What it does:

- inspects repo state and the real diff
- stages only the intended atomic set of files
- generates a descriptive conventional commit message from diff plus user intent
- asks for human approval before creating the commit
- supports splitting one goal into 2-3 atomic commit groups when needed
- asks for human approval before each commit and again before the final push to `origin main`
- creates commits only after approval
- pushes once after all planned commit groups are finished

Examples:

```text
/commit
/commit add pdf preflight analysis
/commit docs for codex command workflow
```

### `/check-ingore-comments`

Use when:

- you want to audit `noqa`, `type: ignore`, or `pyright: ignore` usage

What it does:

- finds suppression comments
- explains why they exist
- recommends whether to keep, remove, or refactor them

Note:

- the filename currently uses `ingore` instead of `ignore`

## Best Practices

- Start broad with `/prime` before jumping into implementation.
- Use `/next-step` when you are unsure what to build next.
- Use `/plan` before `/execute` for anything non-trivial.
- Treat `/plan` as approval-gated by default: investigate first, then review each artifact before continuing.
- Treat OpenSpec artifacts as the planning source of truth.
- Use `/validate` to report reality, not optimism.
- Use `/commit` after validation, not before it.
- Treat `/commit` as approval-gated: approve each commit, then approve one final push.
- Prefer small, localized changes for the first end-to-end workflow trials.

## Good Example Session

For this repository, a strong example is:

```text
/prime pdf preflight analysis
/next-step pdf pipeline
/plan add pdf preflight analysis
/execute add-pdf-preflight-analysis
/validate add-pdf-preflight-analysis
/commit add pdf preflight analysis
```

That is a good workflow trial because it is:

- aligned with the roadmap
- small enough to implement safely
- large enough to exercise all major commands

## Notes

- These commands should stay aligned with real repo state.
- If the workflow changes, update the command file and `.codex/commands/README.md` together in the same change.
- Prefer repo reality over stale assumptions like old test counts or outdated architecture descriptions.
