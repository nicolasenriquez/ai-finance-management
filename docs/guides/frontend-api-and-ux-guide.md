# Frontend API And UX Guide

## Purpose

This guide translates the implemented analytics API into deterministic frontend behavior.
It defines exactly how payloads become UI states, labels, tables, and drill-down interactions.

## API Endpoints

- Summary: `GET /api/portfolio/summary`
- Lot detail: `GET /api/portfolio/lots/{instrument_symbol}`

## Environment And API Prefix Resolution

- Route prefix is configuration-driven by backend `settings.api_prefix`.
- Current default is `/api`.
- Frontend should compose base URLs from environment config and must not hardcode host-specific absolute URLs.

## Response Contracts

### Summary Response

Shape:

- `as_of_ledger_at: datetime`
- `rows: PortfolioSummaryRow[]`

Row fields:

- `instrument_symbol`
- `open_quantity`
- `open_cost_basis_usd`
- `open_lot_count`
- `realized_proceeds_usd`
- `realized_cost_basis_usd`
- `realized_gain_usd`
- `dividend_gross_usd`
- `dividend_taxes_usd`
- `dividend_net_usd`

Behavioral notes:

- Symbols are deterministic and uppercase.
- Summary rows are symbol-sorted.
- Values are ledger-derived only.

### Lot Detail Response

Shape:

- `as_of_ledger_at: datetime`
- `instrument_symbol: str`
- `lots: PortfolioLotDetailRow[]`

Lot fields:

- `lot_id`
- `opened_on`
- `original_qty`
- `remaining_qty`
- `total_cost_basis_usd`
- `unit_cost_basis_usd`
- `dispositions: LotDispositionDetail[]`

Disposition fields:

- `sell_transaction_id`
- `disposition_date`
- `matched_qty`
- `matched_cost_basis_usd`
- `sell_gross_amount_usd`

## Normalization And Formatting Rules

- Symbol:
  - Input to lot detail may contain whitespace or mixed case.
  - UI should render canonical uppercase symbol from response payload.
- Quantity fields:
  - Preserve up to 9 decimals.
  - Trim only trailing zeros in compact contexts.
- Money fields:
  - Display in USD with 2 decimals.
  - Do not infer FX conversions.
- Datetime:
  - Render `as_of_ledger_at` in user locale, with UTC option in tooltip.

## Numeric Handling And Precision Safety

- Treat financial fields as decimals, not binary floating point primitives.
- Do not use JavaScript `Number` for financial aggregation or equality checks.
- Use one decimal-safe utility boundary for parse, compare, and format logic.
- Preserve backend-provided values as source of truth for persisted KPIs.
- If any client-side derived value is required, make rounding mode explicit and match backend policy.
- Rounding policy by field type:
  - quantity-like: 9 decimal places
  - money-like: 2 decimal places
- Formatting must not mutate underlying stored values used for calculations.

## UX State Model

### Summary View States

- `loading`: skeleton rows and timestamp placeholder
- `ready`: table rendered with summary rows
- `empty`: explicit "No portfolio ledger activity found"
- `error`: explicit API error with retry action

### Lot Detail View States

- `loading`: lot row skeleton and symbol chip placeholder
- `ready`: lots + disposition history
- `not_found`: explicit unknown-symbol message (from 404)
- `error`: explicit API error with retry

## Error Handling Contract

- Unknown symbol (`404`) must map to a not-found state, not a generic crash.
- Validation/client failures (`4xx`) should show actionable and concise text.
- Server failures (`5xx`) should show stable fallback UI with retry.
- No silent fallback to stale or inferred values.

### API Error Matrix

| Status | Typical Cause | UI State | User Copy Pattern | Action |
| --- | --- | --- | --- | --- |
| `404` | Symbol not found in persisted ledger | `not_found` | `Instrument {SYMBOL} was not found in the portfolio ledger.` | Provide "Back to Summary" and symbol search/edit affordance |
| `422` | Invalid symbol input or unsafe client request shape | `error` | `The request could not be processed. Review the symbol format and try again.` | Keep user input visible and allow immediate retry |
| `500` | Backend/database failure while serving analytics | `error` | `Portfolio analytics is temporarily unavailable. Please retry.` | Retry button + non-blocking support/debug hint |

Implementation notes:

- Use backend `detail` text as primary error detail where safe for end users.
- Keep message tone factual and concise.
- Do not map all failures to a generic empty state.

## Interaction Patterns

- Summary row click and keyboard activation both open lot detail.
- Lot detail includes "Back to summary" preserving prior table position if possible.
- `as_of_ledger_at` appears in both summary and detail headers.
- Table headers must provide sortable affordances only where backend semantics remain deterministic.

## Recommended Information Architecture

- `/portfolio`
  - grouped summary table
  - global as-of timestamp
  - quick definitions for KPI columns
- `/portfolio/:symbol`
  - lot summary strip
  - lots table
  - nested or expandable dispositions

## Anti-Patterns To Avoid

- Inferring market-value or unrealized return from unsupported data.
- Hiding unknown-symbol failures behind empty lists.
- Mutating raw API values in ways that change financial meaning.
- Overloading the first view with charts before summary correctness is obvious.

## Implementation Readiness Checklist

- Response typing mirrors backend schemas exactly.
- Decimal formatting utilities are centralized and tested.
- Error mapping includes 404-specific behavior.
- Accessibility labels exist for row actions and table context.
- Each page surfaces `as_of_ledger_at`.
