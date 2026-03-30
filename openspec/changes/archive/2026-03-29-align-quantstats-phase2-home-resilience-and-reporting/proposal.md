## Why

The current QuantStats integration is not production-safe yet: Home depends on quant metrics as a hard requirement, and runtime callable mismatches can break the entire page. We need a standards-aligned phase-2 plan that keeps frontend reliability while introducing QuantStats reports and expanded analytics safely.

## What Changes

- Add a repository standard document for QuantStats usage (`docs/standards/quantstats-standard.md`) grounded in official QuantStats documentation and repository fail-fast rules.
- Align backend QuantStats adapter behavior to version-compatible callables and explicit optional-metric behavior so unsupported metrics do not crash the entire quant payload.
- Add a bounded HTML report capability (portfolio and selected symbol/ETF scope) using QuantStats report APIs with explicit generation and retrieval contracts.
- Rebalance Home route reliability so optional quant/reporting modules can fail explicitly at section level without taking down core portfolio context.
- Add explicit placement and routing rules for advanced quant metrics (Home preview vs Risk section vs dedicated Quant/reporting section), including benchmark-omission visibility and report action lifecycle states.
- Add fail-first backend and frontend tests for QuantStats adapter compatibility, section-scoped error rendering, and report contract boundaries.
- Update changelog and product/guides references to reflect final scope, dependency policy, and deferred items.

## Capabilities

### New Capabilities
- `portfolio-quant-reporting`: Generate and deliver bounded QuantStats HTML tearsheets and related report metadata for portfolio and scoped symbol/ETF requests.

### Modified Capabilities
- `portfolio-analytics`: Add resilient QuantStats metric integration behavior and explicit contracts for optional benchmark-relative metrics.
- `frontend-release-readiness`: Extend deterministic state-handling requirements for section-scoped failures in Home/analytics quant modules.

## Impact

- Affected backend areas:
  - `app/portfolio_analytics/service.py`
  - `app/portfolio_analytics/routes.py`
  - `app/portfolio_analytics/schemas.py`
  - `app/portfolio_analytics/tests/`
- Affected frontend areas:
  - `frontend/src/pages/portfolio-home-page/PortfolioHomePage.tsx`
  - `frontend/src/features/portfolio-workspace/`
  - `frontend/src/features/portfolio-hierarchy/`
  - `frontend/src/pages/portfolio-analytics-page/`
- Affected docs/standards:
  - `docs/standards/quantstats-standard.md` (new)
  - `docs/README.md`
  - `CHANGELOG.md`
- Dependencies and governance:
  - QuantStats usage remains pinned and must stay contract-tested against the installed version API surface.
