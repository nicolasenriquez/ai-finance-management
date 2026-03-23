# pgvector Guide

## Status

This guide is optional and future-facing.

`pgvector` is not part of the current MVP baseline because the current product scope explicitly defers AI features and embeddings.

Use this guide only if the product scope changes to include semantic retrieval, similarity search, or embeddings-backed features.

## What `pgvector` Is

`pgvector` is a PostgreSQL extension for storing embeddings and running vector similarity search inside PostgreSQL.

Good fit:

- semantic search over extracted document text
- similarity search across notes, records, or future AI-generated summaries
- embeddings attached to durable relational entities

Poor fit:

- canonical transaction ledger storage
- lot accounting
- ordinary filtering, sorting, and aggregation that standard SQL handles well

## Adoption Criteria

Adopt `pgvector` only when all of the following are true:

- there is a real embeddings use case in the product
- storing vectors in the same PostgreSQL system is simpler than running a separate vector store
- vector freshness, rebuild strategy, and model provenance are defined

Do not add `pgvector` "just in case."

## Environment Requirements

Using `pgvector` requires:

1. installing the extension binaries in the PostgreSQL runtime
2. enabling the extension in the target database

Example:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

Important:

- the current `postgres:18-alpine` image in this repository does not guarantee `pgvector` is installed
- adopting `pgvector` would require a Docker/runtime decision before any migration can rely on it

## Recommended Data Model

If adopted, keep embeddings separate from ledger truth tables.

Preferred pattern:

- base entity table stays relational and authoritative
- embedding table stores:
  - owning entity id
  - embedding vector
  - embedding model id
  - embedding dimension
  - source text version or fingerprint
  - generated timestamp

This keeps embeddings rebuildable and prevents the ledger schema from absorbing AI-specific concerns.

## Query Strategy

Start simple:

- exact filtering in SQL first
- vector similarity second
- hybrid retrieval only if the product actually needs it

Examples of future patterns:

- filter by document type, then similarity search within that slice
- filter by account or instrument domain, then rank by vector distance

## Indexing Strategy

Start with exact or small-scale similarity search first.

When scale requires approximate nearest-neighbor indexing, evaluate:

- HNSW
- IVFFlat

Tradeoffs to document before choosing:

- recall
- index build time
- memory footprint
- query latency
- ingestion/update cost

Do not standardize one ANN index type across the repo before you have an actual workload benchmark.

## Operational Guardrails

- embeddings are derived data and must be rebuildable
- store model provenance so vector meaning is auditable
- define re-embedding triggers before rollout
- avoid coupling embeddings to canonical transaction correctness
- keep vector features out of financial correctness paths

## Decision Rule For This Repository

Use `pgvector` only after the roadmap or PRD explicitly adds an AI or semantic retrieval feature.

Until then:

- keep it out of Docker Compose
- keep it out of migrations
- keep it out of standards required for every contributor

## References

- `pgvector` release note: https://www.postgresql.org/about/news/pgvector-070-released-2852/
- `pgvector` project: https://github.com/pgvector/pgvector
- PostgreSQL `CREATE EXTENSION`: https://www.postgresql.org/docs/18/sql-createextension.html
