# TimescaleDB Guide

## Status

This guide is optional and future-facing.

Use the correct naming:

- Tiger Data: company and documentation brand
- TimescaleDB: PostgreSQL extension for time-series workloads

TimescaleDB is not part of the current repository baseline.

## When TimescaleDB Fits

TimescaleDB is a strong option when the repository begins storing large, append-heavy, time-oriented datasets such as:

- historical `price_history`
- quote snapshots
- market data refresh history
- derived time-bucket analytics over price series

It is not automatically justified for tables that merely contain dates.

## When TimescaleDB Does Not Fit

Do not use TimescaleDB for:

- `source_document`
- `import_job`
- canonical PDF records
- portfolio ledger events
- lots
- lot dispositions

Those tables are ledger and provenance tables, not time-series append stores.

## Adoption Criteria

Adopt TimescaleDB only when:

- market-data volume is large enough that native PostgreSQL indexes and tables become insufficient
- time-bucket queries and retention behavior are clearly valuable
- the team accepts the runtime and extension dependency in local and deployment environments

Do not adopt it only because the finance domain includes historical prices.

## Environment Requirements

Using TimescaleDB requires:

1. installing TimescaleDB binaries in the PostgreSQL runtime
2. enabling the extension in the target database

Example:

```sql
CREATE EXTENSION IF NOT EXISTS timescaledb;
```

Important:

- the current `postgres:18-alpine` image does not include TimescaleDB by default
- self-hosted adoption requires an image/runtime change and a compatibility review for the chosen PostgreSQL version

## Recommended Repository Boundary

If adopted, keep TimescaleDB isolated to genuine market-data tables.

Recommended future candidates:

- `price_history`
- `quote_snapshot`
- maybe high-volume FX history if that becomes part of analytics

Recommended non-candidates:

- transaction truth tables
- accounting-policy tables
- provenance or audit tables

## Feature Areas Worth Using

If market-data scale justifies the extension, evaluate:

- hypertables for append-heavy history
- time bucketing for analytics windows
- continuous aggregates for repeated summary queries
- retention and storage-optimization policies aligned to data freshness needs

Each feature should be justified by a workload, not enabled preemptively.

## Operational Guardrails

- keep ledger truth and time-series storage separate
- define retention policy explicitly before enabling automated lifecycle features
- document refresh cadence and late-arriving data behavior
- avoid making analytics correctness depend on opaque background aggregation behavior

## Decision Rule For This Repository

Use native PostgreSQL first for current MVP and near-term analytics.

Revisit TimescaleDB when:

- price history becomes a large, append-heavy workload
- repeated time-bucket queries become expensive
- retention or rollup policies become operationally necessary

Until then:

- do not require it in Docker Compose
- do not require it in migrations
- do not document it as a baseline dependency

## References

- Tiger Data docs: https://www.tigerdata.com/docs/
- Self-hosted TimescaleDB docs: https://docs.tigerdata.com/self-hosted/latest
- PostgreSQL `CREATE EXTENSION`: https://www.postgresql.org/docs/18/sql-createextension.html
