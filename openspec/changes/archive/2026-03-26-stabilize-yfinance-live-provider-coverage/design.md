## Context

The repository already has a deterministic `yfinance` adapter, staged refresh scopes (`core`, `100`, `200`), and explicit operator evidence contracts. The remaining blocker is no longer the orchestration model; it is live-provider behavior on real symbols. Current smoke evidence shows two concrete patterns:

- `QQQM` can fail with `empty history` under the configured `5y` period, which is consistent with an ETF/security that may not have the requested history window.
- `AMD` and `XLF` can produce valid runtime fetch behavior while still omitting currency metadata, which currently causes a hard failure before persistence.

The repo constraints remain unchanged:

- canonical, ledger, lot, dividend, and corporate-action truth must remain untouched by market-data refresh
- automated tests must remain deterministic and avoid live-provider dependence
- `core` must remain strict for required portfolio coverage
- unsupported provider payloads and explicit invalid currency metadata must still fail fast

## Goals / Non-Goals

**Goals:**

- Recover `empty history` responses through one bounded shorter-period fallback ladder before classifying a symbol as failed.
- Recover missing currency metadata through one explicit operational default currency assignment (`USD`) when price rows are otherwise valid.
- Keep total per-symbol recovery pressure bounded and auditable.
- Extend typed refresh evidence so operators can distinguish retries, history-fallback recoveries, assumed-currency recoveries, and final failures.
- Keep implementation localized to provider config, adapter normalization, refresh orchestration, tests, and operational docs.

**Non-Goals:**

- Adding market-enriched analytics or valuation APIs
- Expanding to broker-authenticated or multi-provider fetch paths
- Relaxing fail-fast behavior for unsupported payloads, required-symbol exhaustion, or explicit invalid currency values
- Adding scheduler, queue, or public route infrastructure

## Decisions

### Decision: Use an ordered shorter-period fallback ladder only for semantic `empty history`

When the configured primary period returns `empty history`, the adapter will retry the same symbol against a configured ordered fallback ladder of shorter periods. The default ladder for this change is `3y -> 1y -> 6mo` after the primary `5y` attempt. The first non-empty result wins; exhausting the ladder remains a symbol failure.

Why this over retrying the same `5y` request repeatedly:

- `empty history` is usually a semantic coverage issue, not a transient transport error.
- Shorter periods directly address newer listings/funds without broadening the provider contract.
- The ladder is deterministic, bounded, and easy to test.

Alternative considered:

- Keep `empty history` terminal forever. Rejected because it blocks Phase 6 on a narrow, predictable provider limitation.

### Decision: Treat missing currency metadata as one explicit operational default to `USD`

If a symbol yields valid day-level price rows but both approved metadata reads (`fast_info`, `info`) still do not provide currency, the adapter may assign a configured default currency code for the current `yfinance` operational path. The default for this change is `USD`. This fallback is allowed only when currency is absent, not when the provider returns an explicit unsupported value.

Why this over continuing to fail hard:

- The current affected symbols are predominantly U.S.-listed instruments in the active universe.
- The fallback is explicit, narrow, auditable, and operationally reversible.
- It unblocks the current provider path without mutating any ledger truth.

Alternative considered:

- Infer currency from exchange/symbol heuristics. Rejected because it is less transparent than one explicit configured operational default.

### Decision: Separate transport retry caps from semantic fallback caps

Existing `max_retries` remains the cap for transient provider/network failures. Semantic recovery caps are controlled separately by the configured period ladder length and single-pass missing-currency fallback. This keeps total symbol pressure bounded and predictable.

Why this over one blended retry loop:

- Transport failures and semantic coverage failures are different failure classes.
- A blended loop obscures why a symbol was retried and makes operator evidence harder to interpret.
- Separate caps make it clear that `empty history` is not retried indefinitely.

Alternative considered:

- Count every fallback as a generic retry. Rejected because it hides the recovery reason and complicates diagnostics.

### Decision: Keep snapshot identity anchored to the requested refresh contract

`snapshot_key` and the top-level refresh identity will remain anchored to the requested refresh configuration (`period`, `interval`, semantic flags, symbol scope, and capture date), even when one or more symbols recover through a shorter fallback period. The actual fallback periods used per symbol will be recorded in snapshot metadata and typed refresh evidence rather than silently redefining snapshot identity.

Why this over deriving snapshot identity from the effective per-symbol fallback mix:

- It preserves the current idempotent snapshot contract and avoids mixed, unstable key semantics.
- It keeps the operator-visible meaning of one refresh run anchored to what was requested, not to internal recovery details.
- It still preserves auditability because symbol-level fallback periods remain explicit in structured evidence.

Alternative considered:

- Recompute snapshot identity from the effective fallback periods used by each symbol. Rejected because it makes key semantics harder to reason about, complicates repeatability, and blurs the difference between requested contract and recovery detail.

### Decision: Surface recovery diagnostics in typed refresh results and snapshot metadata

Refresh results and snapshot metadata will expose which symbols used shorter-history fallback, which fallback period each symbol used, and which symbols used assumed default currency, in addition to existing retry and failed-symbol diagnostics.

Why this over relying on logs only:

- The repo already treats structured run evidence as the operator contract.
- Phase 6 closeout needs machine-readable evidence for smoke comparisons.
- Operators need to distinguish a true clean run from a recovered run.

Alternative considered:

- Leave diagnostics only in logs. Rejected because it weakens the explicit operational evidence contract.

## Risks / Trade-offs

- [Risk] Defaulting missing currency to `USD` can be wrong for a future non-USD symbol. -> Mitigation: keep it configured and explicit, record every assumed-currency symbol in typed evidence, and preserve fail-fast on explicit invalid currency values.
- [Risk] A longer fallback ladder can increase refresh latency. -> Mitigation: keep the ladder short by default and preserve per-symbol spacing as a separate bounded control.
- [Risk] Recovery logic could drift into broad graceful degradation. -> Mitigation: restrict the contract to the observed blocker classes and require deterministic tests for exhaustion and unsupported cases.
- [Risk] `core` could appear healthier than it is if recovered symbols are invisible. -> Mitigation: expose recovery diagnostics in typed outputs and docs.
- [Risk] Mixed effective periods inside one refresh run could confuse snapshot interpretation. -> Mitigation: keep snapshot identity anchored to the requested refresh contract and record actual fallback periods per symbol in metadata/evidence.

## Migration Plan

1. Lock the new contract with failing adapter and service tests for shorter-period fallback, assumed-currency fallback, and recovery diagnostics.
2. Extend typed settings/config and provider config for fallback periods and default currency.
3. Update adapter and refresh orchestration in the smallest slice needed to satisfy the new contract.
4. Update docs and changelog to define the new operational posture and evidence expectations.
5. Run deterministic validation first, then a staged smoke sequence (`core -> 100 -> 200`) to capture post-change evidence.

## Open Questions

- None. The fallback strategy and default-currency posture are fixed for this proposal scope.
