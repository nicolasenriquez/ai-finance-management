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

## Why These References Matter

- The course repo defines the delivery workflow and validation philosophy.
- The golden set defines the extraction contract.
- The library docs define the implementation details and failure modes of the PDF ETL stack.

## Usage Rule

When planning implementation:

- use the course repo for workflow and process structure
- use the golden set for data correctness
- use official library docs for technical implementation details
