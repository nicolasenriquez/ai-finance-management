# scikit-learn Standard: Reproducible Estimator Workflows, Pipelines, and Evaluation Discipline

## Overview

This document defines how to use **scikit-learn** in this repository for classical machine-learning workflows, preprocessing, model selection, and evaluation.

scikit-learn is the canonical estimator framework for tabular ML in this repository when the problem fits its scope.

## Why scikit-learn

- Consistent estimator API (`fit`, `predict`, `transform`).
- First-class pipeline and model-selection workflows.
- Strong official guidance for leakage prevention and reproducibility.
- Mature metric and scoring ecosystem for supervised modeling.

## Scope

Applies to:

- supervised and unsupervised estimator workflows
- preprocessing plus model pipelines
- cross-validation and hyperparameter search
- model persistence under controlled environment contracts

Does not apply to:

- deep learning systems
- reinforcement learning systems
- GPU-first training stacks
- ad hoc modeling code that bypasses estimator contracts without justification

## Dependency Policy

Use repository-managed dependencies and lockfiles.

```bash
uv add scikit-learn
```

Rules:

- Keep version pinning explicit in repository manifests.
- Treat artifacts as version-sensitive and environment-sensitive.

## Core Usage Rules

### 1. Build around estimator contracts

Repository ML components must align with scikit-learn conventions.

Rules:

- Estimators expose `fit`.
- Predictive estimators expose `predict`.
- Transformative components expose `transform`.
- Custom components remain pipeline-compatible.

### 2. Use pipelines for learned preprocessing

Any preprocessing fit from training data must be inside a pipeline.

Includes:

- scaling
- encoding
- imputation
- feature selection
- learned transforms

Do not fit preprocessing on full data before splits.

### 3. Prevent leakage by construction

Leakage prevention is mandatory.

Rules:

- Split data before fitting learned transforms.
- Fit transforms on training folds only in CV.
- Keep evaluation data isolated from training-time statistics.
- Use pipeline-aware search objects for tuned workflows.

### 4. Make heterogeneous preprocessing explicit

Categorical and numeric handling must be explicit and reviewable.

Rules:

- Do not rely on implicit mixed-type coercion.
- Use explicit encoding and imputation policies.
- Keep feature mapping logic centralized.

### 5. Reproducibility requires explicit randomness control

Set `random_state` wherever supported.

Rules:

- Set `random_state` on stochastic estimators.
- Set `random_state` on splitters/search procedures as needed.
- Do not rely on ambient global randomness.

### 6. Metrics must match the business objective

Scoring selection must be explicit.

Rules:

- Do not rely on `.score()` by default if objective differs.
- Define scoring metric explicitly in model-selection code.
- For imbalanced tasks, avoid accuracy-only evaluation.

### 7. Hyperparameter search must stay estimator-native

Approved patterns:

- `GridSearchCV`
- `RandomizedSearchCV`
- CV-aware search over complete pipelines

Rules:

- Tune full pipelines when preprocessing affects model behavior.
- Keep grids/distributions bounded and reviewable.
- Avoid undocumented manual sweeps as production evidence.

### 8. Persistence is an environment contract

Persisting a model requires metadata for reproducibility.

Required context:

- code revision
- dependency versions
- feature schema
- training data snapshot/reference
- selected metric and validation results

Do not assume cross-version artifact portability.

### 9. Respect scikit-learn problem boundaries

If the use case is fundamentally deep learning/RL/GPU-centric, use the appropriate stack instead of stretching scikit-learn.

## Approved Workflow

### 1. Split data early

Create train/validation/test boundaries before fitting learned preprocessing.

### 2. Build explicit preprocessing

Keep numeric and categorical preprocessing explicit and schema-aware.

### 3. Compose pipeline

```python
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.ensemble import RandomForestClassifier

numeric_features = ["age", "income"]
categorical_features = ["segment", "region"]

numeric_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="median")),
    ("scaler", StandardScaler()),
])

categorical_pipeline = Pipeline([
    ("imputer", SimpleImputer(strategy="most_frequent")),
    ("encoder", OneHotEncoder(handle_unknown="ignore")),
])

preprocess = ColumnTransformer([
    ("num", numeric_pipeline, numeric_features),
    ("cat", categorical_pipeline, categorical_features),
])

model = Pipeline([
    ("preprocess", preprocess),
    ("estimator", RandomForestClassifier(random_state=42)),
])
```

### 4. Evaluate with explicit scoring

```python
from sklearn.model_selection import cross_val_score

scores = cross_val_score(
    model,
    X_train,
    y_train,
    cv=5,
    scoring="roc_auc",
)
```

### 5. Tune with pipeline-aware search

```python
from sklearn.model_selection import GridSearchCV

param_grid = {
    "estimator__n_estimators": [100, 300],
    "estimator__max_depth": [None, 10, 20],
}

search = GridSearchCV(
    estimator=model,
    param_grid=param_grid,
    cv=5,
    scoring="roc_auc",
    n_jobs=-1,
)
```

## Custom Component Rules

- Keep constructor params explicit.
- Learn state in `fit`, not `__init__`.
- Preserve pipeline compatibility.
- Implement only required interfaces.

## Data Rules

- Feature schema is contract-bound and versioned.
- Missing-value policy must be explicit.
- Categorical encoding policy must be explicit.
- Train/inference column semantics must be stable.

## Evaluation Rules

- Preserve strict train/test separation.
- Prefer CV for model comparison.
- Compare models under same split strategy and scoring objective.
- Distinguish optimization metric vs reporting metrics.

## Anti-patterns

Do not:

- fit scalers/encoders on full dataset pre-split
- compare models under mismatched folds without documentation
- rely on implicit estimator defaults for critical scoring
- persist artifacts without version/context metadata
- use scikit-learn outside its intended problem boundary

## Validation Commands

```bash
uv run ruff check .
uv run mypy app/
uv run pyright app/
uv run pytest -v
```

Add deterministic regression tests when schema, preprocessing, metrics, or persistence contracts change.

## Resources (Official)

- User guide: https://scikit-learn.org/stable/user_guide.html
- Common pitfalls: https://scikit-learn.org/stable/common_pitfalls.html
- Developer estimator guidance: https://scikit-learn.org/stable/developers/develop.html
- Model persistence: https://scikit-learn.org/stable/model_persistence.html
- Metrics and scoring: https://scikit-learn.org/stable/modules/model_evaluation.html
- Hyperparameter tuning: https://scikit-learn.org/stable/modules/grid_search.html
- FAQ (0.21): https://scikit-learn.org/0.21/faq.html
- Documentation versions: https://scikit-learn.org/dev/versions.html

---

**Last Updated:** 2026-04-18
