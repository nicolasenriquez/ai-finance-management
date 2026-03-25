Run iterative local CI healing until gates pass or a real blocker is reached.

Optional input: `@ARGUMENTS`

Supported call shapes:
- `/self-heal-ci`
- `/self-heal-ci target=fast|full`
- `/self-heal-ci using=back|front|all`
- `/self-heal-ci scope=back|front|all` (alias)
- `/self-heal-ci max=<int>`
- `/self-heal-ci autofix=on|off`
- `/self-heal-ci target=full using=all max=5 autofix=on`

Defaults:
- `target=full`
- `using=all` (`scope=all` alias)
- `max=5`
- `autofix=on`

## Goal

Converge local CI gates to green using minimal, iterative fixes:
- run the right CI target (`fast` or `full`) on selected scope (`using=back|front|all`)
- detect the first failing gate
- apply the smallest safe fix
- rerun and repeat until pass or blocked

This command may modify code and docs when needed to fix failing gates.

## Target + Scope Semantics (`using`/`scope`)

`target=fast`:
- `using=back` (`scope=back`) -> `just backend-ci-fast`
- `using=front` (`scope=front`) -> `just frontend-ci`
- `using=all` (`scope=all`) -> `just ci-fast`

`target=full`:
- `using=back` (`scope=back`) -> `just backend-ci`
- `using=front` (`scope=front`) -> `just frontend-ci`
- `using=all` (`scope=all`) -> `just ci`

Why `target=full using=all` as default:
- matches your final pre-push confidence gate
- includes the complete local CI posture

## Guardrails

- Do not run destructive git commands.
- Do not commit or push.
- Do not silence type/lint/security/test failures to force green.
- Keep fixes minimal and localized to failing gates.
- Stop if failure is clearly environmental (DB down, missing tool, network policy, missing secrets).
- If the same failure signature repeats twice with no meaningful progress, stop and report `BLOCKED`.

## Process

### 1) Preflight

Run:

```bash
pwd
git rev-parse --abbrev-ref HEAD
git status --short
```

Check required tools:

```bash
command -v just || true
command -v uv || true
command -v npm || true
```

If `just` is missing, use explicit fallback commands (see step 3 fallback map).

### 2) Optional auto-fix warmup (`autofix=on`)

Run:

```bash
just format
just precommit-run
```

If `precommit-run` fails on non-fixable checks, continue to iterative loop (do not stop here).

### 3) Iterative healing loop (up to `max`)

For each iteration:

1. Run the selected pipeline for `(target, using/scope)`.
2. If green, finish.
3. If red, isolate first failing gate by running the smallest sequence:

Backend gates:

```bash
just lint
just type
just security
just test
just test-integration
```

Frontend gates:

```bash
just frontend-lint
just frontend-type
just frontend-test
just frontend-build
```

Pre-push hooks (when target includes full `ci`):

```bash
just precommit-run-prepush
```

4. Apply smallest safe fix for the first failing gate:
- lint/format failures -> run `just format`, then targeted adjustments
- type failures -> minimal type-safe code edits, then rerun `just type`
- security failures -> minimal secure fix, rerun `just security`
- test failures -> minimal behavior fix + tests, rerun failing test target
- hook-only failures -> fix hook findings only, rerun hook target

5. Rerun only the previously failing gate first, then rerun pipeline phase.

Fallback map when `just` is unavailable:
- backend lint: `uv run ruff check .` + `uv run black . --check --diff`
- backend format: `uv run ruff check . --fix` + `uv run black .`
- backend type: `uv run mypy app/ && uv run pyright app/ && uv run ty check app`
- backend security: `uv run bandit -c pyproject.toml -r app --severity-level high --confidence-level high` + `uv run pip-audit --progress-spinner=off --ignore-vuln CVE-2026-4539`
- backend tests: `uv run pytest -v -m "not integration"` and integration with `uv run pytest -v -m integration`
- frontend lint/type/test/build: `cd frontend && npm run <script>`

### 4) Stop conditions

Return `PASS` when target is fully green.

Return `PARTIAL PASS` when:
- selected scope converges partially but environment-only blockers remain for required gates.

Return `BLOCKED` when:
- environment blockers prevent progress (DB/tool/network/credentials)
- repeated same failure signature with no progress.

Return `FAIL` when:
- iteration limit reached without convergence.

## Output Format

```text
Self-heal CI scope:
- target: fast|full
- using/scope: back|front|all
- max iterations: <n>
- autofix: on|off

Iteration log:
- iter 1: <phase> -> pass/fail -> fix applied: <summary>
- iter 2: <phase> -> pass/fail -> fix applied: <summary>
...

Final gate status:
- selected pipeline: pass/fail/blocked
- overall: PASS | PARTIAL PASS | BLOCKED | FAIL

Files touched:
- <list>

Key blockers or findings:
- <bullets>

Next action:
- PASS -> /commit-local
- PARTIAL PASS or BLOCKED -> exact blocker fix command(s)
- FAIL -> /review-fix (if reviewer findings exist) or focused manual fix plan
```

## Definition of Done

The command is done when:
- selected target reached `PASS`, or
- a concrete `BLOCKED` reason is proven, or
- iteration cap reached with explicit `FAIL` report.

In all cases, output must include:
- what was run
- what was fixed
- what remains
- one exact next command.
