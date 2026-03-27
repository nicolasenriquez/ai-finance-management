## Why

Phase 6 operator verification is currently too expensive for the practical local environment. The repository already proves the core market-refresh path, but full-scope `100` and `200` verification create disproportionate runtime and CPU pressure, which turns routine validation into an operational rabbit hole and blocks progress toward the next product step.

## What Changes

- Rebalance market-refresh verification so `core` remains the required operational path for current portfolio truth.
- Remove routine `200` verification from the current readiness contract and stop treating it as an expected local validation lane.
- Reduce the readiness role of full-scope `100` verification by promoting a lighter representative non-core smoke lane as the default broader-scope safeguard.
- Keep any broader-than-core verification explicitly optional/manual unless the repository is in a deliberate soak or tuning pass.
- Update integration-test markers, local workflow commands, validation guidance, and product planning docs so the lighter verification posture is the documented source of truth.
- Preserve current refresh persistence semantics and snapshot identity; this change does not add incremental backfill or watermark-based refresh behavior.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `market-data-operations`: narrow the verification and smoke-readiness contract so `core` remains required, `200` is removed from routine verification, and representative non-core coverage replaces full-scope expansion as the default broader validation posture.

## Impact

- OpenSpec change artifacts for verification-scope rebalancing.
- Market-data integration tests, pytest markers, and `just` command surfaces tied to heavy refresh coverage.
- Validation and operator documentation, including market-data runbook guidance and baseline command expectations.
- Product planning/history documentation (`roadmap`, `backlog`, `decisions`, `CHANGELOG`) so Phase 6 readiness reflects the lighter contract.
- No backend API, persistence schema, or refresh-semantic changes are expected in this change.
