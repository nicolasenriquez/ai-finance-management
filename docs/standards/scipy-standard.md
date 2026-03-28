# SciPy Standard: Scientific Algorithms, Optimization, and Statistical Rigor

## Overview

This document defines how to use **SciPy** in this repository for numerical algorithms that go
beyond core NumPy operations, especially optimization, statistics, and linear algebra tasks used by
portfolio analytics and risk estimation.

SciPy usage must remain deterministic, auditable, and bounded by explicit assumptions.

## Why SciPy

- Production-grade scientific algorithms built on NumPy.
- Broad module coverage (`optimize`, `stats`, `linalg`, `sparse`, `signal`, etc.).
- Strong interoperability with NumPy arrays and pandas-prepared inputs.
- Mature documentation on parallel execution and thread-safety caveats.

## Scope

Applies to:

- risk-estimator kernels requiring statistical distributions or optimizers
- advanced numerical routines beyond basic vectorized algebra
- sparse and dense linear-algebra operations where algorithm choice matters

Does not apply to:

- basic element-wise arithmetic (prefer NumPy)
- dataframe shaping and table semantics (prefer pandas)

## Installation and Dependency Policy

Use repository-managed dependencies and lockfiles:

```bash
uv add scipy
```

Notes:

- Keep SciPy versions pinned through `pyproject.toml` and `uv.lock`.
- Introduce optional accelerator dependencies only after profiling and approval.

## Import and API Usage Rules

### 1. Use explicit SciPy submodule namespaces

- Prefer explicit namespace usage such as `import scipy.optimize as spo` or `from scipy import stats`.
- Follow SciPy's import guidance to keep call sites clear and grep-friendly.

### 2. Treat solver outputs as contracts, not assumptions

- For optimizers and root-finders, always validate status fields (`success`, message/status code,
  convergence metrics) before using outputs.
- Fail explicitly when solver convergence is not achieved.

### 3. Keep algorithm assumptions documented

- Record distribution assumptions, objective definitions, bounds, and constraints.
- Do not hide default-method behavior when the chosen method affects financial interpretation.

### 4. Choose dense vs sparse paths intentionally

- Use sparse APIs when matrices are sparse by design.
- Avoid implicit conversion between sparse/dense representations in hot paths.

## Parallelism and Thread Safety Rules

- SciPy defaults to single-threaded function execution; however, operations may call BLAS/LAPACK
  backends that use multiple threads.
- Use documented `workers=` parameters when available for supported parallelizable routines.
- Treat shared mutable data as unsafe without explicit synchronization.
- Respect SciPy thread-safety caveats for sparse matrices/arrays and spatial trees during mutation.

## Testing Rules

- Validate numeric outputs with explicit tolerance (`rtol`, `atol`) and deterministic fixtures.
- Include failure-path tests for non-convergence and invalid input domains.
- Ensure estimator contracts surface clear errors rather than silent fallback values.

## Validation Commands

SciPy-backed logic is validated with repository gates:

```bash
uv run pytest -v
uv run mypy app/
uv run pyright app/
uv run ty check app
```

## Resources (Official)

- SciPy docs index: https://docs.scipy.org/doc/scipy/
- User guide/tutorial index: https://docs.scipy.org/doc/scipy/tutorial/index.html
- Installation: https://scipy.org/install/
- API reference index: https://docs.scipy.org/doc/scipy/reference/index.html
- Import guidelines: https://docs.scipy.org/doc/scipy/reference/index.html#guidelines-for-importing-functions-from-scipy-subpackages
- `scipy.optimize.minimize`: https://docs.scipy.org/doc/scipy/reference/generated/scipy.optimize.minimize.html
- Thread safety: https://docs.scipy.org/doc/scipy/tutorial/thread_safety.html
- Parallel execution support: https://docs.scipy.org/doc/scipy/tutorial/parallel_execution.html

---

**Last Updated:** 2026-03-28
