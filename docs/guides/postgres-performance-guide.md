# PostgreSQL Performance Guide

## Purpose

This guide explains how to investigate and improve PostgreSQL performance in this repository without guessing.

Use this guide when:

- an API endpoint becomes slow
- a migration or rebuild job takes too long
- a query plan looks suspicious
- table growth changes query behavior

This guide is operational. For repository rules, use `docs/standards/postgres-standard.md`.

## Performance Philosophy

- Measure before tuning.
- Optimize the real query, not a hypothetical one.
- Prefer query-shape fixes and index fixes before global configuration changes.
- Change one variable at a time.

The linked Medium article is useful as a checklist of common ideas, but official PostgreSQL documentation remains the primary authority.

## Step 1: Capture The Real Query

Before changing anything, identify:

- the exact SQL statement
- the execution frequency
- the request or job path that triggered it
- the data volume involved

If the problem is caused by repeated small queries, solve the application query pattern before tuning PostgreSQL settings.

## Step 2: Inspect The Query Plan

Start with:

```sql
EXPLAIN SELECT ...;
```

Then move to:

```sql
EXPLAIN ANALYZE SELECT ...;
```

For deeper diagnosis:

```sql
EXPLAIN (ANALYZE, BUFFERS) SELECT ...;
```

Look for:

- sequential scans on large tables
- unexpected sorts
- nested loops over large inputs
- bad cardinality estimates
- repeated heap fetches
- high shared-buffer reads or disk reads

## Step 3: Check Existing Index Coverage

Ask:

- Does the query filter on a column that is already indexed?
- Does it sort in a way that a current index can satisfy?
- Does it filter and sort across multiple columns that should be indexed together?
- Is the query only interested in a small subset that could use a partial index?

In this repository, current single-column indexes are a good starting point, but future analytics paths may need composite indexes that match actual sort and filter order.

## Step 4: Choose The Smallest Effective Fix

### Query rewrite

Prefer this when:

- the query fetches more rows than needed
- filtering happens too late
- repeated queries can be collapsed into one

### New or revised index

Prefer this when:

- the query shape is stable
- selectivity is good
- plan evidence shows scanning or sorting overhead

### Batch writes

Prefer this when:

- inserts or updates are currently executed row by row
- ingestion volume has grown enough that round-trip cost matters

### Materialized view or precomputed table

Prefer this when:

- a read-heavy analytics query repeats the same heavy join or aggregation
- freshness requirements are weaker than raw transaction truth

## Index Selection Guide

### Single-column B-tree

Use for:

- exact equality lookups
- simple range filters
- small-table sorting hot paths

### Multicolumn B-tree

Use for:

- queries that repeatedly filter by one column and sort by another
- stable access patterns such as `WHERE source_document_id = ? ORDER BY event_date, id`

Order matters. Match the most common filter and sort pattern rather than collecting columns at random.

### Partial index

Use for:

- a narrow hot subset such as active rows, open lots, or a specific event type if that subset becomes materially smaller than the full table

### Expression index

Use for:

- immutable computed predicates you actually query, such as normalized text or date bucketing logic

### `INCLUDE` columns

Use for:

- read-heavy queries that benefit from index-only scans and repeatedly fetch a few extra columns

### BRIN

Use for:

- very large append-ordered time-series tables where rows stay physically correlated with time

Do not use BRIN on small or frequently reshaped tables.

## Maintenance And Statistics

### Autovacuum

Autovacuum is the baseline maintenance mechanism. Suspect vacuum or analyze lag when:

- plans suddenly degrade after a large write volume change
- dead tuples accumulate
- a table grows quickly but planner estimates remain inaccurate

### `ANALYZE`

Use manual `ANALYZE` carefully when you have changed data distribution significantly and need planner statistics refreshed sooner.

### `pg_stat_statements`

Enable and use `pg_stat_statements` when you need to identify the real high-cost queries over time rather than inspecting one request in isolation.

Typical workflow:

```sql
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;
SELECT query, calls, total_exec_time, mean_exec_time
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;
```

## Memory And Connection Tuning

### `work_mem`

Use per-session or targeted tuning when a specific sort or hash operation is spilling to disk.

Do not raise it globally without understanding concurrent query pressure.

### Connection pooling

Introduce PgBouncer only when concurrent connection count becomes a real problem.

This repository does not currently justify PgBouncer by default. The current app uses SQLAlchemy async with a bounded pool and simple local Compose deployment.

## Repository-Specific Hotspots To Watch

As analytics grows, pay attention to:

- canonical record rebuild queries ordered by `event_date, id`
- ledger rebuild queries filtered by `source_document_id`
- future portfolio analytics aggregations by symbol, lot state, or pricing snapshot
- future `price_history` or quote refresh workloads once market data becomes large

## What Not To Do

- do not tune from a blog checklist without plan evidence
- do not add five indexes when one composite index is the real need
- do not start with partitioning while the dataset is still small
- do not globally increase memory settings because one query is slow
- do not use TimescaleDB or `pgvector` as a substitute for sound schema design

## Escalation Path

Use this order when a performance issue appears:

1. inspect query count and query shape
2. inspect `EXPLAIN (ANALYZE, BUFFERS)`
3. verify statistics and autovacuum health
4. add or refine indexes
5. batch writes or precompute repeated analytics
6. consider connection pooling or extension adoption only if the workload justifies it

## References

- PostgreSQL 18 `EXPLAIN`: https://www.postgresql.org/docs/18/using-explain.html
- PostgreSQL 18 indexes: https://www.postgresql.org/docs/18/indexes.html
- PostgreSQL 18 `CREATE INDEX`: https://www.postgresql.org/docs/18/sql-createindex.html
- PostgreSQL 18 routine vacuuming: https://www.postgresql.org/docs/18/routine-vacuuming.html
- PostgreSQL 18 monitoring stats: https://www.postgresql.org/docs/18/monitoring-stats.html
- Medium article for secondary context: https://medium.com/@vikas95prasad/postgresql-performance-optimisation-practical-techniques-that-actually-move-the-needle-ab1eb9f8a830
