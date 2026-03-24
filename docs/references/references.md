# References

## Source of Truth

Primary methodology source:

- local sibling repo: `../agentic-coding-course`

Most relevant course modules for this project:

- Module 5: PRD, template setup, planning workflow
- Module 7: validation pyramid, code review, system review
- Module 12: parallel implementation after patterns are stable

## Product Source of Truth

Current product truth for the extraction MVP:

- `docs/product/prd.md`
- `docs/product/decisions.md`
- `app/golden_sets/dataset_1/202602_stocks.pdf`
- `app/golden_sets/dataset_1/202602_stocks.json`

## Extraction and Validation Libraries

- pdfplumber: https://github.com/jsvine/pdfplumber
- Camelot: https://camelot-py.readthedocs.io/
- PyMuPDF: https://pymupdf.readthedocs.io/
- Pydantic models: https://docs.pydantic.dev/latest/concepts/models/
- Pydantic validators: https://docs.pydantic.dev/latest/concepts/validators/
- Pandera: https://pandera.readthedocs.io/en/stable/dataframe_schemas.html
- Great Expectations: https://docs.greatexpectations.io/
- pytest parametrization: https://docs.pytest.org/en/stable/how-to/parametrize.html
- Bandit docs: https://bandit.readthedocs.io/
- Black docs: https://black.readthedocs.io/
- ty docs: https://docs.astral.sh/ty/
- ty repository: https://github.com/astral-sh/ty

## Market Data Exploration References (Official)

Validated on 2026-03-24 before documenting the ETF exploration note.

- yfinance documentation index: https://ranaroussi.github.io/yfinance/index.html
- yfinance repository and legal usage notes: https://github.com/ranaroussi/yfinance
- Yahoo terms link referenced by yfinance: https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm
- Yahoo terms of service: https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html
- Yahoo terms index: https://policies.yahoo.com/us/en/yahoo/terms/index.htm
- pandas `DataFrame.pct_change`: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html
- pandas `DataFrame.resample`: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
- pandas `DataFrame.ewm`: https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html

## External Template Evaluations

- vstorm full-stack AI agent template (evaluation note):
  - source template: https://github.com/vstorm-co/full-stack-ai-agent-template
  - local evaluation: `docs/references/full-stack-ai-agent-template-evaluation.md`

Reference-only rule:

- external templates are evaluated as pattern sources, not as drop-in implementation authorities
- adoption must be phase-scoped, standards-aligned, and test-backed

## Database and PostgreSQL References

Primary authority for database behavior:

- PostgreSQL 18 docs: https://www.postgresql.org/docs/18/
- PostgreSQL 15 docs index: https://www.postgresql.org/docs/15/index.html
- PostgreSQL indexes: https://www.postgresql.org/docs/18/indexes.html
- PostgreSQL multicolumn indexes: https://www.postgresql.org/docs/18/indexes-multicolumn.html
- PostgreSQL `CREATE INDEX`: https://www.postgresql.org/docs/18/sql-createindex.html
- PostgreSQL `EXPLAIN`: https://www.postgresql.org/docs/18/using-explain.html
- PostgreSQL `CREATE EXTENSION`: https://www.postgresql.org/docs/18/sql-createextension.html
- PostgreSQL routine vacuuming: https://www.postgresql.org/docs/18/routine-vacuuming.html
- PostgreSQL client authentication: https://www.postgresql.org/docs/18/client-authentication.html
- PostgreSQL `pg_hba.conf`: https://www.postgresql.org/docs/18/auth-pg-hba-conf.html
- PostgreSQL password authentication: https://www.postgresql.org/docs/18/auth-password.html
- PostgreSQL roles: https://www.postgresql.org/docs/18/user-manag.html
- PostgreSQL `GRANT`: https://www.postgresql.org/docs/18/sql-grant.html
- PostgreSQL default privileges: https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html
- PostgreSQL schemas and privileges: https://www.postgresql.org/docs/18/ddl-schemas.html
- PostgreSQL function security: https://www.postgresql.org/docs/18/perm-functions.html

Optional extension references:

- `pgvector` release note: https://www.postgresql.org/about/news/pgvector-070-released-2852/
- `pgvector` project: https://github.com/pgvector/pgvector
- Tiger Data docs: https://www.tigerdata.com/docs/
- Self-hosted TimescaleDB docs: https://docs.tigerdata.com/self-hosted/latest

Secondary background only:

- PostgreSQL performance article: https://medium.com/@vikas95prasad/postgresql-performance-optimisation-practical-techniques-that-actually-move-the-needle-ab1eb9f8a830
- PostgreSQL 7.0 security page, historical only: https://www.postgresql.org/docs/7.0/security.htm
- Tiger Data PostgreSQL security guide: https://www.tigerdata.com/learn/guide-to-postgresql-security
- Tiger Data developer security guide: https://dev.to/tigerdata/postgresql-security-best-practices-a-developers-guide-47f7

## Portfolio and Analytics Reference Repositories

Primary external inspiration for the next project phases:

- doughbox: https://github.com/alxjpzmn/doughbox
- ghostfolio: https://github.com/ghostfolio/ghostfolio
- Stock-P-L: https://github.com/willychang21/Stock-P-L
- Portfolio Performance: https://github.com/portfolio-performance/portfolio
- Ascend: https://github.com/rajatpatel92/portfolio-app

Secondary references:

- stonks-overwatch: https://github.com/ctasada/stonks-overwatch
- visualfolio: https://github.com/benvigano/visualfolio
- investment-dashboard: https://github.com/nmfretz/investment-dashboard
- wealth-warden: https://github.com/nootey/wealth-warden

## Reference Priority

Use the repositories by concern rather than trying to copy one full stack directly.

- `doughbox`: ingestion model, unified storage, deduplication, quote separation
- `ghostfolio`: domain modeling, mature analytics boundaries, production-grade product structure
- `Stock-P-L`: practical solo-builder MVP patterns and transaction-first analytics
- `Portfolio Performance`: accounting depth, importer logic, financial edge cases
- `Ascend`: advanced analytics ideas after the ledger and accounting rules are stable

## Usage Rules For External Repositories

- use external repositories as design references, not as implementation authorities
- prefer copying concepts, boundaries, and test ideas over copying stack choices
- convert useful lessons into one of:
  - a PRD rule
  - an accepted decision
  - a backlog item
  - executable tests or constraints
- avoid creating hidden dependency on any external repo's internal conventions

## Why These References Matter

- The course repo defines the delivery workflow and validation philosophy.
- The golden set defines the extraction contract.
- The library docs define the implementation details and failure modes of the PDF ETL stack.
- The PostgreSQL and extension docs define the authoritative behavior for schema, indexing, extensions, and performance work.
- The portfolio references help define the ledger, pricing, and analytics direction once ingestion is stable.

## Usage Rule

When planning implementation:

- use the course repo for workflow and process structure
- use the golden set for data correctness
- use official library docs for technical implementation details
- use official PostgreSQL and extension docs for database behavior and performance decisions
- use external portfolio repos for architecture and analytics inspiration only after mapping them to this repo's scope
