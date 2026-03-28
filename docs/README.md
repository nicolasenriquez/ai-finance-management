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
  - linting, formatting, security, typing, testing, logging, and database standards
- `docs/references/`
  - external references and supporting research links

## Navigation

- Product: `docs/product/prd.md`
- Frontend product addendum: `docs/product/frontend-mvp-prd-addendum.md`
- Frontend UX/analytics expansion roadmap: `docs/product/frontend-ux-analytics-expansion-roadmap.md`
- Backlog: `docs/product/backlog-sprints.md`
- Validation baseline: `docs/guides/validation-baseline.md`
- Frontend architecture guide: `docs/guides/frontend-architecture-guide.md`
- Frontend API and UX guide: `docs/guides/frontend-api-and-ux-guide.md`
- Frontend design system guide: `docs/guides/frontend-design-system-guide.md`
- Frontend delivery checklist: `docs/guides/frontend-delivery-checklist.md`
- Local workflow (`just`): `docs/guides/local-workflow-justfile.md`
- Logging standard: `docs/standards/logging-standard.md`
- Frontend standard: `docs/standards/frontend-standard.md`
- NumPy standard: `docs/standards/numpy-standard.md`
- pandas standard: `docs/standards/pandas-standard.md`
- SciPy standard: `docs/standards/scipy-standard.md`
- Yfance standard: `docs/standards/yfance-standard.md`
- PostgreSQL standard: `docs/standards/postgres-standard.md`
- PostgreSQL local setup guide: `docs/guides/postgres-local-setup.md`
- PostgreSQL performance guide: `docs/guides/postgres-performance-guide.md`
- PostgreSQL security guide: `docs/guides/postgres-security-guide.md`
- YFinance integration guide: `docs/guides/yfinance-integration-guide.md`
- YFinance financial documents and fundamentals guide: `docs/guides/yfinance-financial-documents-and-fundamentals-guide.md`
- `pgvector` guide: `docs/guides/pgvector-guide.md`
- TimescaleDB guide: `docs/guides/timescaledb-guide.md`
- External references: `docs/references/references.md`
- Frontend references: `docs/references/frontend-references.md`
- Ultimate React Course SOT analysis: `docs/references/ultimate-react-course-frontend-sot-analysis.md`
- ETF exploration note: `docs/references/etf-yfinance-research-notes.md`
- External template evaluation: `docs/references/full-stack-ai-agent-template-evaluation.md`

## Maintenance Rule

When adding new documentation:

- put all `*-standard.md` files in `docs/standards/`
- put product and planning documents in `docs/product/`
- put implementation or operational walkthroughs in `docs/guides/`
- put external source collections in `docs/references/`
