# ETF YFinance Research Notes

## Purpose

This note records how to use the local ETF exploration script at
`/Users/NicolasEnriquez/Downloads/dashboard_etfs.py` as documentation-only research context.

It is not a production implementation reference and does not change current scope.

## Scope Alignment

- Current roadmap keeps portfolio analytics responses ledger-only.
- Market-data provider integration remains a later step (Sprint 5.2).
- This note is an input for that later step, not a trigger to implement provider ingestion now.

## Official Validation Sources

Validated on 2026-03-24:

- yfinance docs: https://ranaroussi.github.io/yfinance/index.html
- yfinance repository (including legal usage disclaimer): https://github.com/ranaroussi/yfinance
- Yahoo terms links referenced by yfinance:
  - https://policies.yahoo.com/us/en/yahoo/terms/product-atos/apiforydn/index.htm
  - https://legal.yahoo.com/us/en/yahoo/terms/otos/index.html
  - https://policies.yahoo.com/us/en/yahoo/terms/index.htm
- pandas APIs used by the notebook logic:
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.pct_change.html
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.resample.html
  - https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.ewm.html

## What Adds Value

- Useful exploratory indicator set for discussion:
  - daily and monthly returns
  - SMA/EMA trend context
  - Bollinger Bands
  - Ichimoku components
- Useful prompt-template ideas for human-readable analysis narratives.
- Useful candidate ticker focus for MVP continuity with dataset 1 symbols:
  - `AMD, APLD, BBAI, BRK.B, GLD, GOOGL, HOOD, META, NVDA, PLTR, QQQM, SCHD, SCHG, SMH, SOFI, SPMO, TSLA, UUUU, VOO`

## Why It Stays Documentation-Only

The current script is exploratory and not production-safe for this repository:

- contains notebook magics (`!pip install`) and is not executable as a normal module
- has a hardcoded ticker path in multi-ticker logic
- uses at least one incorrect return formula (`cum_return` computed from price levels)
- mixes data retrieval, indicator derivation, and recommendation prompting in one flow
- has no deterministic fixtures, no service boundary, and no repo-aligned tests

## Minimal Recommended Adoption Path (Later Phase)

When Sprint 5.2 begins, use this notebook only as raw input and then:

- define a provider adapter boundary under the market-data slice
- keep fail-fast behavior for provenance, symbol normalization, and duplicate semantics
- enforce deterministic tests for time-series transforms
- start with dataset-1 symbol coverage before expanding universes
- keep legal usage boundaries explicit in docs and operational decisions
