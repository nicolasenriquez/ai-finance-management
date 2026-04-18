# Agent Kit Import

This document mirrors the intended `.codex/skills/agent-kit/` folder that could not be written directly in this sandbox because hidden `.codex` writes are blocked.

Use `agent-kit` as the short, representative folder name if you install the pack locally.

## Included Skills

- `context-engineering` - gather the right repo context before planning or coding.
- `idea-refine` - turn a vague request into a concrete product direction.
- `spec-driven-development` - write proposal, design, specs, and tasks before coding.
- `planning-and-task-breakdown` - split a change into executable slices.
- `incremental-implementation` - implement the smallest safe vertical slice.
- `test-driven-development` - write the failing test first, then fix, then refactor.
- `frontend-ui-engineering` - design route structure, layout, chart composition, and hierarchy.
- `api-and-interface-design` - define stable typed boundaries and response states.
- `browser-testing-with-devtools` - verify UI behavior in a real browser.
- `debugging-and-error-recovery` - reproduce, isolate, and repair failures.
- `code-review-and-quality` - review for correctness, regressions, and missing tests.
- `code-simplification` - reduce duplication and noise without changing behavior.
- `performance-optimization` - measure before optimizing, then re-check.
- `security-and-hardening` - harden inputs, contracts, and trust boundaries.
- `git-workflow-and-versioning` - keep branches and commits clean.
- `documentation-and-adrs` - capture durable decisions and changelog-worthy changes.
- `source-driven-development` - prefer repository docs and primary sources over guesswork.
- `shipping-and-launch` - validate, clean up, and prepare handoff.

## Suggested Folder Layout

```text
.codex/skills/agent-kit/
  README.md
  context-engineering/SKILL.md
  idea-refine/SKILL.md
  spec-driven-development/SKILL.md
  planning-and-task-breakdown/SKILL.md
  incremental-implementation/SKILL.md
  test-driven-development/SKILL.md
  frontend-ui-engineering/SKILL.md
  api-and-interface-design/SKILL.md
  browser-testing-with-devtools/SKILL.md
  debugging-and-error-recovery/SKILL.md
  code-review-and-quality/SKILL.md
  code-simplification/SKILL.md
  performance-optimization/SKILL.md
  security-and-hardening/SKILL.md
  git-workflow-and-versioning/SKILL.md
  documentation-and-adrs/SKILL.md
  source-driven-development/SKILL.md
  shipping-and-launch/SKILL.md
```

## Recommended Use

Use this pack when the task is:

- planning-heavy
- implementation-heavy
- UI-sensitive
- test-sensitive
- delivery-sensitive

It pairs well with the repo's OpenSpec workflow and command guide.
