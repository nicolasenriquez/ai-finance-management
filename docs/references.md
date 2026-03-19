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

- `docs/prd.md`
- `docs/decisions.md`
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
- The portfolio references help define the ledger, pricing, and analytics direction once ingestion is stable.

## Usage Rule

When planning implementation:

- use the course repo for workflow and process structure
- use the golden set for data correctness
- use official library docs for technical implementation details
- use external portfolio repos for architecture and analytics inspiration only after mapping them to this repo's scope
