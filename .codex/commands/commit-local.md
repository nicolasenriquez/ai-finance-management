Create one clean local commit from the current working tree and stop before any push.

Optional input: `@ARGUMENTS`

Use this command as the local packaging step after implementation and validation when the user wants to push manually later.

## Goal

Inspect staged, unstaged, and untracked changes, review whether they form one coherent local commit, stage the full intended working tree, generate a descriptive commit message from the real diff plus optional user intent, create the local commit, and stop before any push action.

## Input Rule

- Treat `@ARGUMENTS` as extra naming intent, not as the source of truth.
- The real source of truth for the commit message is:
  - `git status --short --branch`
  - `git status --porcelain`
  - `git diff HEAD`
  - `git diff --cached`
- If the input and the diff disagree, trust the diff and report the mismatch.

## Workflow

### 1. Inspect repo state first

Run:

```bash
git status --short --branch
git status --porcelain
git diff HEAD
git diff --cached
```

If there are no changes, stop and report that there is nothing to commit.

### 2. Inspect recent history for style continuity

Run:

```bash
git log -10 --oneline
```

Use this only to keep commit style consistent. Do not copy old messages blindly.

### 3. Review the full working tree

Review all current change types together:

- staged changes
- unstaged tracked changes
- untracked files

Decide whether they form one coherent local commit.

If the working tree is clearly mixed across unrelated goals, stop and explain what should be split out first.

### 4. Stage the intended full local change

If the working tree is one coherent unit, stage everything intended for the local commit.

Run:

```bash
git add -A
```

Then verify the staged result:

```bash
git status --short
git diff --cached --stat
git diff --cached
```

Do not silently exclude files if they are part of the same intended local change.

### 5. Generate the commit message

Create a descriptive conventional commit message grounded in the actual staged diff.

Use a prefix such as:

- `feat`
- `fix`
- `docs`
- `chore`
- `refactor`
- `test`

Rules:

- subject line must be concise and specific
- add a body when it materially improves clarity
- describe the behavioral or repository outcome, not just filenames
- use `@ARGUMENTS` only to improve specificity

### 6. Create the local commit

Before running `git commit`, show:

- the files that will be included
- the final commit message
- a short summary of the change

Then create the commit.

Run:

```bash
git commit -m "<subject>" -m "<body-if-needed>"
```

If a body is not needed, use a single `-m`.

### 7. Stop before push

Do not run any push command.

Do not ask for push approval.

Do not suggest that push already happened.

The command must end after reporting:

- branch
- commit hash
- final commit message
- push status: not run

## Safeguards

- Refuse to continue if there are no changes.
- Refuse to continue if the diff appears to contain unrelated work that should be split.
- Do not invent a commit message without reading the diff.
- Do not claim validation passed unless it was actually run.
- Do not run `git push`.
- Do not ask for push approval because push is outside the scope of this command.
- Prefer one clean local commit over one noisy local commit.

## Output Format

Use this structure:

```text
Commit readiness:
- ready / blocked

Commit summary:
- <high-level summary>

Commit message:
- <final subject>
- <final body if any>

Local commit result:
- branch: <branch>
- status: created / blocked / failed
- commit: <hash or none>

Push status:
- not run

Next action:
- <exact manual next step, usually `git push origin <branch>` if the user wants to publish it later>
```

## Guardrails

- Do not invent a commit message without reading the diff.
- Do not claim validation passed unless it was actually run.
- Do not create multiple commits unless the diff clearly requires split packaging.
- Do not run `git push`.
- Do not hide mixed or unrelated changes.
- Prefer one clean local commit over one noisy local commit.
