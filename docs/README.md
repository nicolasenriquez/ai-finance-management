# Documentation Index

This repository organizes documentation by function so standards, product artifacts, guides, and reference material are easy to find.

## Structure

- `docs/product/`
  - product and delivery source documents
  - `prd.md`, `roadmap.md`, `decisions.md`, `backlog-sprints.md`
- `docs/guides/`
  - implementation and workflow guides used during delivery
  - extraction, validation, and domain-specific guidance
- `docs/standards/`
  - all repository standards live together here
  - linting, formatting, security, typing, testing, and logging standards
- `docs/references/`
  - external references and supporting research links

## Navigation

- Product: `docs/product/prd.md`
- Backlog: `docs/product/backlog-sprints.md`
- Validation baseline: `docs/guides/validation-baseline.md`
- Logging standard: `docs/standards/logging-standard.md`
- External references: `docs/references/references.md`

## Maintenance Rule

When adding new documentation:

- put all `*-standard.md` files in `docs/standards/`
- put product and planning documents in `docs/product/`
- put implementation or operational walkthroughs in `docs/guides/`
- put external source collections in `docs/references/`
