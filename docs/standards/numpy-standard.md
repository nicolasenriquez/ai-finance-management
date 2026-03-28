# NumPy Standard: Array Computing, Determinism, and Type Safety

## Overview

This document defines how to use **NumPy** in this repository for deterministic numeric
computation, especially for analytics and risk-estimator kernels.

NumPy is the canonical low-level array engine in the Python scientific stack and must be used in
a way that preserves reproducibility, explicit failure behavior, and strict typing expectations.

## Why NumPy

- Efficient vectorized math on homogeneous arrays.
- Broadcasting and ufunc support for fast element-wise operations.
- Strong interoperability with SciPy and pandas.
- Official typing support via `numpy.typing`.

## Scope

Applies to:

- estimator math kernels and numeric transforms in backend services
- deterministic test fixtures and numeric comparison assertions
- typed array interfaces in internal utility modules

Does not apply to:

- tabular ETL orchestration (prefer pandas)
- high-level optimization/statistical algorithms (prefer SciPy)

## Installation and Dependency Policy

Use repository-managed dependencies and lockfiles:

```bash
uv add numpy
```

Notes:

- Keep NumPy versioning pinned through repository manifests/lockfiles.
- Do not install ad hoc global versions outside project dependency management.

## Core Usage Rules

### 1. Prefer vectorized operations and ufuncs over Python loops

- Use NumPy operations that execute in compiled code paths.
- Avoid per-element Python loops for estimator kernels unless profiling proves no practical
  vectorized alternative.

### 2. Use broadcasting intentionally

- Broadcasting is valid when trailing dimensions are equal or one is `1`.
- Treat unexpected broadcast expansion as a correctness risk and fail fast with explicit shape
  checks.
- Avoid patterns that create large implicit intermediate arrays.

### 3. Control copy vs view behavior explicitly

- Basic slicing typically returns views; advanced indexing creates copies.
- Use explicit `.copy()` when mutation isolation is required.
- For diagnostics, use `arr.base` only to determine view/copy relationship, not object lifetime.

### 4. Make dtype decisions explicit

- Set dtypes deliberately for financial computations.
- Avoid unsafe implicit casting across estimator paths.
- Where conversion is required, prefer explicit `astype(...)` calls and document precision intent.

### 5. Reproducible randomness in tests and simulations

- Use `np.random.default_rng(seed)` as the standard RNG entrypoint.
- Do not rely on implicit global random state for deterministic validations.

## Concurrency and Thread Safety

- NumPy supports multithreaded usage, and many operations release the GIL.
- Shared mutable arrays across threads are a data-race risk; prefer read-only sharing or explicit
  locking.
- Operations on `dtype=np.object_` generally do not release the GIL and are poor candidates for
  thread-based speedups.

## Typing Standard

Use NumPy typing aliases in strict-typed modules:

- `numpy.typing.NDArray`
- `numpy.typing.ArrayLike`
- `numpy.typing.DTypeLike`

For mypy-heavy modules where platform-specific scalar precision matters, NumPy documents a mypy
plugin path. Adoption remains optional and must be justified by concrete typing failures.

## Testing Rules

- Use numeric tolerance assertions for floating-point comparisons.
- Prefer `numpy.testing.assert_allclose` for array comparisons over `==` checks on floats.
- Keep tolerance values explicit (`rtol`, `atol`) per domain requirement.

## Validation Commands

NumPy-specific checks are covered by repository gates; use these during implementation:

```bash
uv run pytest -v
uv run mypy app/
uv run pyright app/
```

## Resources (Official)

- NumPy user guide: https://numpy.org/devdocs/user/index.html
- NumPy installation: https://numpy.org/install/
- Broadcasting: https://numpy.org/devdocs/user/basics.broadcasting.html
- Copies and views: https://numpy.org/devdocs/user/basics.copies.html
- Typing (`numpy.typing`): https://numpy.org/devdocs/reference/typing.html
- Random `Generator` / `default_rng`: https://numpy.org/devdocs/reference/random/generator.html
- Thread safety: https://numpy.org/devdocs/reference/thread_safety.html
- `numpy.testing.assert_allclose`: https://numpy.org/devdocs/reference/generated/numpy.testing.assert_allclose.html

---

**Last Updated:** 2026-03-28
