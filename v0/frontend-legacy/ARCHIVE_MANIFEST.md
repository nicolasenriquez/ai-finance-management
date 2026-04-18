# Frontend Legacy Archive Manifest

Date: 2026-04-17
OpenSpec change: `archive-v0-and-build-compact-trading-dashboard`
Task slice: `2.1`
Archive path: `v0/frontend-legacy/`

## Purpose

Preserve the full pre-reset frontend implementation before replacing active `frontend/`
with a compact-foundation scaffold.

## Source And Archive Rules

- Source copied from: repo-root `frontend/` as it existed immediately before task `2.1`.
- Excluded runtime artifacts:
  - `node_modules/`
  - `dist/`
  - `.vite/`
  - `.vite-temp/`
  - `*.tsbuildinfo`
- Archive copy command:
  - `rtk rsync -a --delete --exclude node_modules --exclude dist --exclude .vite --exclude .vite-temp --exclude '*.tsbuildinfo' frontend/ v0/frontend-legacy/`

## Preserve/Move Intents For Rebuild

- Preserve behavior contracts:
  - hierarchy pivot behavior
  - quant report lifecycle behavior
  - explicit lifecycle state surfaces (`loading`, `empty`, `stale`, `unavailable`, `error`)
  - typed finance-safe formatters/utilities
- Move/demote in new shell:
  - dense/advanced diagnostics to progressive disclosure
  - full report route into compact utility dock

## Notes

- This archive is immutable baseline evidence for rollback and behavior comparison during
  compact-dashboard implementation tasks `2.x-5.x`.
