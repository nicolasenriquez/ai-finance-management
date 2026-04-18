# Compact Trading Dashboard Implementation Handoff

## Date
2026-04-18

## Scope

Change:

- `archive-v0-and-build-compact-trading-dashboard`

Covered implementation slices:

- archive/foundation: `2.1-2.3`
- IA and route delivery: `3.1-3.9`
- route and governance hardening: `4.1-4.17`
- documentation/validation closeout: `5.1-5.4`

## Completion Snapshot

The rebuilt active frontend is now a compact five-route shell:

1. `/portfolio/home`
2. `/portfolio/analytics`
3. `/portfolio/risk`
4. `/portfolio/signals`
5. `/portfolio/asset-detail/:ticker`

Preserved behavior surfaces:

- hierarchy pivot interaction model
- compact quant report utility with scope/date controls and explicit lifecycle states
- explicit module/shell lifecycle-state communication

Key hardening delivered:

- responsive contracts at `320`, `768`, `1024`, `1440` without horizontal overflow
- semantic route-token aliases for surface, border, spacing, typography, radius
- explicit primary-module state feedback (`empty`, `unavailable`, `success`, `error`, retry)
- bounded state ownership (`local_ui`, `url_state`, `server_state`) with URL-backed report controls

## Source Policy Decisions (Final)

- `yfinance` remains phase-primary source.
- `pandas` remains deterministic transformation/derivation layer only.
- Direct/derived/unavailable policy governs every surfaced research metric.
- Non-native proprietary signal labels are explicit `unavailable` until custom contracts are implemented.
- Provenance metadata (`source_id`, `as_of`, `freshness_state`, `confidence_state`) is treated as decision-safety UI, not optional metadata.

### Extraction and Derivation Map

Direct extraction families:

- OHLCV/time-series and corporate actions
- option-chain implied volatility context
- valuation/quality screener-backed fields where coverage exists

Derived families (pandas):

- ATR
- moving-average regime
- rolling returns and benchmark spread
- drawdown depth/duration
- correlation and return-distribution summaries

Explicitly non-native in this phase:

- `J5`, `JR4`
- green-on-green / red-on-red labels
- native historical IV percentile feed
- custom exhaustion labels without declared deterministic contract

## Route-Specific Chart Grammar

- `home`: compact trend + table/card summary, no tactical candlestick emphasis
- `analytics`: performance line, attribution waterfall, consistency heatmap, drill-down tables
- `risk`: drawdown timeline, distribution view, risk/return scatter, correlation/concentration tables
- `signals`: ranked tactical review lists and bounded technical tables
- `asset-detail`: candlestick/price-action and price-volume combo dominance allowed only here

## Validation Evidence

Frontend gates:

- `rtk npm --prefix frontend run test` (pass, 23 files / 47 tests)
- `rtk npm --prefix frontend run lint` (pass)
- `rtk npm --prefix frontend run build` (pass)

OpenSpec gates:

- `rtk openspec validate "archive-v0-and-build-compact-trading-dashboard" --type change --strict --json` (valid: true)
- `rtk openspec instructions apply --change "archive-v0-and-build-compact-trading-dashboard" --json` (`state: all_done`, `38/38` tasks complete)

## Archive-Specific Tooling Notes

- OpenSpec telemetry flush emits non-blocking DNS errors for `edge.openspec.dev` in this environment; command results for status/instructions/validate remain usable and successful.
- Frontend lint is configured as strict TypeScript no-emit checks for app/node tsconfig projects (`lint` and `type-check` equivalently gate type correctness).

## Residual Risks and Follow-Up

1. Source-contract coverage remains incomplete for proprietary/non-native signal labels; keep explicit `unavailable` rendering until backend contracts exist.
2. Continue documenting symbol-level coverage variability for yfinance fundamentals fields to avoid implied universality.
3. Preserve route-level contract tests as guardrails before adding any new module family to the compact shell.
