# Codex Commands Beginner Guide

This is a beginner-friendly map for the repo-local Codex commands.
It mirrors the recommended `.codex/commands/README.md` content.

## Quick Path

If you are not sure what to run, use this order:

1. `/prime` when you are starting fresh or lost in context.
2. `/next-proposal` when you want to decide what feature or change should exist next.
3. `/change-ready` when you want the full proposal-to-plan flow with human approval gates.
4. `/plan <change>` when the proposal already exists and you want an implementation plan.
5. `/next-step` when a change already exists and you want the best next task.
6. `/execute <change> [task]` when you are ready to code and test.
7. `/validate` when you want to check what is actually passing.
8. `/commit-local` when the work is done and you want a safe local checkpoint.

## Simple Rule

- If you are deciding, use `/next-proposal` or `/next-step`.
- If you are organizing work, use `/plan`.
- If you are writing code, use `/execute`.
- If you are checking quality, use `/validate`, `/review-fix`, or `/explain`.

## Command Cheat Sheet

| Command | Best for | When to use |
|---|---|---|
| `/prime` | repo preflight | Start of a session or after context loss |
| `/next-proposal` | choosing the next change | When you do not yet know what proposal to create |
| `/change-ready` | guided proposal-to-plan flow | When you want the repo to prepare a change with human approval gates |
| `/new-branch` | branch creation | Before generating proposal artifacts for a new change |
| `/plan` | execution planning | When a proposal already exists and needs task slicing |
| `/next-step` | implementation sequencing | When a change exists and you want the best next task |
| `/explain` | task understanding | When you want to understand a slice before coding it |
| `/execute` | implementation | When you are ready to make code changes for a task slice |
| `/review-fix` | review-driven repair | When review findings need a minimal fix plan |
| `/self-heal-ci` | CI recovery | When local checks are failing and you want iterative repair |
| `/validate` | quality report | When you want to see what actually passes or is blocked |
| `/commit-local` | local checkpoint | When work is done and you want a clean local commit only |
| `/commit` | final packaging | When the change is verified and ready to package for delivery |

## Beginner Tips

- Use `/prime` before anything else if the repo context feels stale.
- Use `/next-proposal` for a new idea and `/next-step` for an already approved change.
- Use `/plan` before `/execute`; do not jump straight to coding on a large change.
- Use `/validate` after implementation so you know what is truly green.
- Use `/commit-local` only after you are satisfied with the local state.
