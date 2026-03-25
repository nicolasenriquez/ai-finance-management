# Market Data Provider Standard

## Purpose

This standard defines non-negotiable rules for integrating external market-data providers in this repository.

It exists to preserve:

- ledger-first transaction truth
- explicit provenance and idempotency
- fail-fast behavior
- deterministic market-data ingestion

## Scope

Applies to:

- provider adapters under `app/market_data`
- provider configuration and credentials
- provider fetch, normalization, and ingestion flows
- market-data operational documentation and validation evidence

Does not apply to:

- canonical transaction normalization (`pdf` pipeline)
- ledger event derivation rules
- valuation KPI expansion

## Source Priority

Use sources in this order:

1. Official provider documentation and API references
2. Official provider repository docs and legal notices
3. Repository contracts (`docs/product/*`, `docs/guides/*`, `app/market_data/*`)
4. Secondary tutorials/articles for context only

Secondary sources must not define repository behavior.

## Boundary Rules

- Provider data must flow into `market_data_snapshot` and `price_history`, not transaction-ledger tables.
- Provider ingestion must not create, mutate, or delete canonical/ledger/lot truth.
- Provider-specific quirks must stay inside adapters and must not leak into canonical transaction contracts.

## Provenance and Idempotency Rules

- Every write must include explicit source identity (`source_type`, `source_provider`).
- Every write must include deterministic snapshot identity (`snapshot_key`, `snapshot_captured_at`).
- Every price row must include exactly one market-time key (`market_timestamp` xor `trading_date`).
- In-request duplicate symbol/time rows must be rejected explicitly.
- Repeated provider ingests for same snapshot/row key must resolve deterministically (insert-or-update), never ambiguous append behavior.

## Symbol and Time Rules

- Symbol forms must preserve canonical dataset-1 shapes (including dotted symbols such as `BRK.B`).
- Symbol rewrites that lose meaning are forbidden.
- Snapshot and market timestamps must be timezone-aware when timestamp fields are used.

## Fail-Fast Rules

- Missing required provider metadata or key fields must fail explicitly.
- Unsafe symbol mapping must fail explicitly.
- Unknown provider configuration or missing credentials must fail explicitly.
- Silent defaults that hide provider/data defects are forbidden.

## Operational Rules

- Use explicit timeout values for provider fetch operations.
- Define bounded retry policy for transient provider/network failures.
- Log provider fetch, normalize, ingest start/completion/failure with structured event names.
- Preserve enough context in logs to audit which provider snapshot was used.

## Security and Secrets Rules

- API keys/secrets must come from environment configuration, never hardcoded.
- Secrets must not be logged.
- Local development defaults must be explicit and non-production.

## Testing and Validation Rules

- Unit tests must cover normalization, symbol/time validation, and duplicate handling.
- Integration tests must prove non-mutation of canonical/ledger truth.
- CI tests should use deterministic fixtures/mocks for provider responses rather than live provider calls.
- Live/manual verification can exist, but cannot be the only evidence path.

## Documentation Rules

- Provider-specific assumptions and limitations must be documented explicitly.
- If provider behavior is approximate or unofficial, document risk and fallback strategy.
- Any provider integration change must update:
  - `docs/references/references.md`
  - relevant guide(s)
  - `CHANGELOG.md`

## References

- yfinance docs: https://ranaroussi.github.io/yfinance/index.html
- yfinance functions reference: https://ranaroussi.github.io/yfinance/reference/yfinance.functions.html
- yfinance advanced docs: https://ranaroussi.github.io/yfinance/advanced/index.html
- yfinance repository/legal notice: https://github.com/ranaroussi/yfinance
