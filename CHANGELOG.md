# Changelog

All notable changes to this repository are documented here.

This changelog is designed for both human readers and AI agents.
Entries must remain concise, factual, and structured.

## Entry Format

Use this structure for new entries:

```md
## YYYY-MM-DD

### <type>(<scope>): <short title>
- Summary: <what changed>
- Why: <intent/business or engineering reason>
- Files: <key files/areas>
- Validation: <tests/checks run, or blocked reason>
- Notes: <optional constraints/follow-up>
```

`type` guidance: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`.

## 2026-03-19

### feat(pdf-canonical): add dataset 1 canonical normalization and verification slices
- Summary: Implemented `pdf_normalization` and `pdf_verification` service/route slices to convert extracted dataset 1 rows into typed canonical records and produce deterministic mismatch reports against the checked-in golden contract.
- Why: Freeze trusted canonical contracts and verification evidence before starting PostgreSQL persistence and deduplication work.
- Files: `app/pdf_normalization/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/pdf_verification/{schemas.py,service.py,routes.py,tests/test_service.py}`, `app/main.py`, `openspec/changes/add-dataset-1-canonical-normalization-and-verification/tasks.md`.
- Validation: `uv run pytest -v app/pdf_normalization/tests app/pdf_verification/tests` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass), `uv run black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (no issues).
- Notes: Verification record pairing now uses deterministic fallback identity (`table_name` + `row_index` + `source_page`) so `splits` rows reconcile even when golden rows omit `row_id`.

### docs(reference-guides): record canonical baseline completion and persistence boundary
- Summary: Updated extraction and validation reference guides to reflect that extraction, normalization, and verification are implemented for dataset 1 while persistence remains pending.
- Why: Keep operational docs aligned with delivered behavior and avoid stale guidance that still marks canonical processing as unimplemented.
- Files: `docs/reference-guides/pdf-extraction-guide.md`, `docs/reference-guides/validation-baseline.md`.
- Validation: Documentation reviewed against current `app/pdf_extraction`, `app/pdf_normalization`, `app/pdf_verification` implementations and task checklist status.

## 2026-03-18

### chore(validation): integrate Black and Bandit as required baseline gates
- Summary: Added Black and Bandit as first-class validation layers in tooling/config and propagated the baseline command set across repo guidance and command docs.
- Why: Ensure formatting and security scanning are enforced consistently alongside Ruff, MyPy, Pyright, and pytest rather than remaining documentation-only guidance.
- Files: `pyproject.toml`, `uv.lock`, `.python-version`, `.codex/commands/{README.md,plan.md,execute.md,validate.md}`, `AGENTS.md`, `README.md`, `docs/reference-guides/validation-baseline.md`, `docs/ruff-standard.md`, `docs/black-standard.md`, `docs/backlog-sprints.md`, `app/main.py`.
- Validation: `uv run ruff check .` (pass), `uv run --python 3.12.6 black . --check --diff` (pass), `uv run bandit -c pyproject.toml -r app --severity-level medium --confidence-level medium` (pass), `uv run mypy app/` (pass), `uv run pyright app/` (pass), `uv run pytest -q` (100 passed).
- Notes: Added scoped `# nosec B104` on intentional dev bind in `app/main.py` to align Bandit with existing `# noqa: S104` policy.

### docs(quality-gates): add Black and Bandit standards for validation and security
- Summary: Added dedicated standards documentation for Black and Bandit, including configuration baselines, command usage, gate policy, and integration guidance with existing Ruff/MyPy/Pyright/Pytest workflow.
- Why: Formalize how to adopt Black and Bandit in a controlled way using official tooling guidance while keeping repository validation rules explicit and reproducible.
- Files: `docs/black-standard.md`, `docs/bandit-standard.md`, `docs/references.md`, `README.md`.
- Validation: Documentation-only update; content reviewed against official Black and Bandit docs and current repository validation structure.

### feat(pdf_extraction): add deterministic pdfplumber extraction from stored uploads
- Summary: Implemented `app/pdf_extraction` service and `/api/pdf/extract` route to parse dataset 1 tables from stored PDFs with deterministic row order, provenance, and explicit header/footer filtering.
- Why: Complete Sprint 1 Item 1.3 extraction slice before normalization/persistence work.
- Files: `app/pdf_extraction/service.py`, `app/pdf_extraction/routes.py`, `app/pdf_extraction/schemas.py`, `app/pdf_extraction/tests/test_service.py`, `app/pdf_extraction/tests/test_routes.py`, `app/main.py`, `pyproject.toml`, `docs/reference-guides/pdf-extraction-guide.md`.
- Validation: `uv run pytest -v app/pdf_extraction/tests` (6 passed), `uv run mypy app/` (pass), `uv run pyright app/` (0 errors), `uv run ruff check .` (pass).
- Notes: Current scope is raw extraction only; canonical mapping/normalization and persistence remain out of scope for this slice.

## 2026-03-17

### docs(commands): require explicit blast-radius and blind-spot diagnosis in /plan
- Summary: Tightened `/plan` so planning must explicitly diagnose blast radius and blind spots, and must state whether `CHANGELOG.md` updates are required.
- Why: Reduce hidden planning risk and make downstream contract propagation visible before implementation starts.
- Files: `.codex/commands/plan.md`, `.codex/commands/README.md`.
- Validation: Documentation review against current planning workflow and repo governance rules.

### docs(commands): overhaul OpenSpec command workflow and add /explain
- Summary: Reworked command docs for `/prime`, `/plan`, `/execute`; added `/explain`; synchronized command README.
- Why: Improve execution control, planning rigor, and repo-fit guidance for AI-assisted workflow.
- Files: `.codex/commands/prime.md`, `.codex/commands/plan.md`, `.codex/commands/execute.md`, `.codex/commands/explain.md`, `.codex/commands/README.md`.
- Validation: Documentation-only change; reviewed command coverage and examples.

## 2026-03-08

### docs: refine Codex command workflow guidance
- Summary: Updated command-layer documentation and workflow guidance.
- Why: Improve consistency and operator clarity.
- Files: Command docs and related guidance files.
- Validation: Documentation review.

### feat(pdf_ingestion): add PDF ingestion endpoint with preflight and local storage
- Summary: Added PDF ingestion flow with preflight validation and local storage behavior.
- Why: Enable end-to-end upload and preflight path for PDF workflows.
- Files: `app/pdf_ingestion/*`, routing/config/tests.
- Validation: Change tasks completed in OpenSpec; validation executed in implementation flow.

### feat(pdf_preflight): add PDF preflight analysis endpoint
- Summary: Introduced API support for PDF preflight analysis.
- Why: Provide validation and metadata extraction before downstream processing.
- Files: PDF preflight feature modules and tests.
- Validation: Feature validation executed during implementation cycle.

### feat(workflow): add Codex workflow commands and approval-gated commit flow
- Summary: Added repo-local command workflow for prime/plan/execute/validate/commit.
- Why: Standardize AI-assisted delivery process and approval checkpoints.
- Files: `.codex/commands/*`.
- Validation: Command documentation and flow checks.
