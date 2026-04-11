# portfolio-analytics Specification

## Purpose
TBD - created by archiving change add-portfolio-analytics-api-from-ledger. Update Purpose after archive.
## Requirements
### Requirement: Portfolio summary API groups analytics by instrument from ledger truth
The system SHALL provide a portfolio summary API that groups analytics by `instrument_symbol` using persisted portfolio-ledger and lot state rather than reparsing PDFs or accepting client-supplied portfolio totals.

#### Scenario: Grouped summary returns one row per instrument with open position or realized activity
- **WHEN** the analytics service reads the current portfolio state
- **THEN** it returns one summary row per `instrument_symbol` present in persisted ledger truth
- **THEN** each row is derived from `lot`, `lot_disposition`, `portfolio_transaction`, and `dividend_event` data as applicable

### Requirement: Portfolio analytics responses expose explicit ledger-state consistency metadata
The system SHALL include explicit ledger consistency metadata in grouped summary, lot-detail, and newly added chart-oriented analytics responses so clients can determine the persisted ledger state used for computation.

#### Scenario: Summary, lot detail, and chart responses include ledger as-of metadata
- **WHEN** the system returns grouped summary, lot detail, or chart-oriented portfolio analytics responses
- **THEN** the payload includes explicit ledger-state consistency metadata
- **THEN** clients can determine the persisted ledger state time used for computation

### Requirement: Portfolio summary API exposes only ledger-supported KPI fields in v1
The system SHALL expose only analytics fields that are fully supported by current ledger truth, persisted market-data boundaries, and frozen accounting policy, without silently inventing unsupported price-dependent or FX-dependent values.

#### Scenario: Summary row includes only approved KPI and market-enriched fields
- **WHEN** a grouped portfolio summary row is returned
- **THEN** it includes approved ledger and bounded market-enriched fields defined by the active portfolio analytics contract
- **THEN** unsupported FX-sensitive or inferred valuation fields are excluded and represented through explicit failure or nullability semantics

### Requirement: Lot detail API explains per-instrument lot state from ledger truth
The system SHALL provide a lot detail API for one `instrument_symbol` that returns explainable lot rows derived from ledger truth and linked disposition history.

#### Scenario: Lot detail returns explainable lots for one instrument
- **WHEN** a client requests lot detail for an existing `instrument_symbol`
- **THEN** the system returns the lots opened for that instrument with their remaining quantity and basis fields
- **THEN** the response includes enough linked disposition detail to explain how sell-side activity consumed prior lots

### Requirement: Lot detail symbol matching is normalized and deterministic
The system SHALL normalize lot-detail symbol inputs by trimming whitespace and matching case-insensitively, while preserving one canonical uppercase symbol representation in the response.

#### Scenario: Lot detail resolves case and whitespace variants
- **WHEN** a client requests lot detail with a symbol variant such as mixed case or surrounding whitespace
- **THEN** the system resolves it against persisted ledger truth using normalized symbol matching
- **THEN** the response uses the canonical uppercase symbol representation

### Requirement: Analytics APIs remain read-only over the ledger
The system SHALL keep analytics API behavior read-only and must not mutate canonical, ledger, lot, or market-data state while serving summary or lot-detail responses.

#### Scenario: Portfolio analytics request does not change ledger truth
- **WHEN** a client requests grouped summary or lot detail
- **THEN** the system reads persisted ledger and lot data only
- **THEN** it does not create, update, or delete canonical, ledger, lot, or market-data rows as part of the request

### Requirement: Analytics APIs do not trigger rebuild side effects
The system SHALL not trigger portfolio-ledger rebuild operations during analytics request handling and SHALL only consume already-persisted derived ledger state.

#### Scenario: Analytics request does not invoke rebuild
- **WHEN** a client requests grouped summary or lot detail
- **THEN** the system does not call ledger rebuild operations
- **THEN** stale or missing derived ledger state remains an explicit upstream issue instead of an implicit analytics-side mutation

### Requirement: Analytics APIs fail explicitly for unsupported symbol requests
The system SHALL reject unsupported or unknown lot-detail requests with explicit client-facing failure instead of ambiguous empty success when the requested instrument cannot be resolved safely, and frontend consumers SHALL map this response to a dedicated not-found UI state.

#### Scenario: Lot detail rejects unknown instrument symbol
- **WHEN** a client requests lot detail for an `instrument_symbol` that has no matching persisted ledger truth
- **THEN** the system returns an explicit client error
- **THEN** the response makes clear that the requested instrument was not found in the portfolio ledger
- **THEN** frontend consumers display a not-found state rather than an empty success table

### Requirement: Portfolio summary API exposes explicit pricing provenance for market-enriched KPIs
The system SHALL include explicit market-data provenance in grouped portfolio summary responses whenever market-enriched valuation fields are present, so clients can identify which persisted market-data snapshot produced the valuation results.

#### Scenario: Summary response includes pricing provenance
- **WHEN** the system returns a grouped portfolio summary response with market-enriched valuation fields
- **THEN** the payload includes explicit pricing provenance such as the selected snapshot identity and pricing timestamp context
- **THEN** clients can distinguish ledger-state freshness from market-data freshness

### Requirement: Portfolio summary API uses one consistent persisted market-data snapshot per response
The system SHALL compute market-enriched grouped summary KPIs from one explicit persisted market-data snapshot rather than mixing independently selected latest rows across symbols.

#### Scenario: Summary valuation uses one selected snapshot
- **WHEN** the system computes a grouped portfolio summary with market-enriched KPI fields
- **THEN** all price-backed valuation fields in that response are derived from the same selected persisted market-data snapshot
- **THEN** the response does not mix valuation rows from different snapshot identities

### Requirement: Portfolio summary API fails explicitly when required open-position price coverage is incomplete
The system SHALL reject market-enriched grouped summary responses when an instrument with open quantity in the portfolio does not have safe pricing coverage in the selected persisted market-data snapshot.

#### Scenario: Required open-position symbol is missing from selected snapshot
- **WHEN** the system cannot find safe persisted price coverage in the selected snapshot for an instrument whose grouped summary row has open quantity greater than zero
- **THEN** the grouped summary request fails explicitly
- **THEN** the system does not silently omit valuation fields, mix fallback rows from another snapshot, or report a partial portfolio valuation as complete

### Requirement: Portfolio analytics API SHALL provide chart-ready portfolio time-series
The system SHALL provide a read-only portfolio time-series endpoint that returns ordered portfolio value and PnL points for approved periods so frontend chart modules can render trend analytics without client-side inference.

#### Scenario: Time-series endpoint returns ordered points for selected period
- **WHEN** a client requests portfolio time-series for a supported window
- **THEN** the API returns chronologically ordered points with explicit timestamps and value fields
- **THEN** the payload is deterministic for the same persisted input state and period parameters

### Requirement: Portfolio analytics time-series responses SHALL expose explicit temporal interpretation metadata
The system SHALL include explicit temporal interpretation metadata for chart-oriented time-series responses, including at minimum frequency context, timezone basis, and selected period/window parameters.

#### Scenario: Time-series payload includes temporal context metadata
- **WHEN** the API returns chart-oriented time-series data
- **THEN** the response includes explicit temporal interpretation metadata required to render and compare points correctly
- **THEN** frontend consumers do not infer hidden frequency or timezone defaults

### Requirement: Portfolio analytics API SHALL provide contribution breakdown by instrument for selected periods
The system SHALL provide a contribution breakdown endpoint that returns per-symbol aggregates for the selected period to support attribution visualizations.

#### Scenario: Contribution endpoint returns per-symbol aggregates
- **WHEN** a client requests contribution analytics for a supported period
- **THEN** the API returns one row per instrument symbol with contribution-related aggregates
- **THEN** totals are derived from persisted ledger and approved market-data inputs only

### Requirement: Portfolio chart analytics endpoints SHALL enforce a bounded v1 period enum
The system SHALL support only the approved v1 chart period enum (`30D`, `90D`, `252D`, `MAX`) for time-series and contribution analytics requests and SHALL reject unsupported period values explicitly.

#### Scenario: Unsupported chart period is rejected explicitly
- **WHEN** a client requests chart analytics with a period outside the approved v1 enum
- **THEN** the API returns an explicit client-facing validation failure
- **THEN** the service does not coerce unsupported periods into implicit defaults

### Requirement: Quant metrics endpoint SHALL be version-compatible with pinned QuantStats API surface
The system SHALL compute QuantStats-backed metrics through an explicit adapter contract that matches the pinned runtime QuantStats API surface, and SHALL fail explicitly when adapter compatibility checks detect unsupported call paths.

#### Scenario: Adapter-compatible metrics are returned successfully
- **WHEN** a client requests quant metrics for a supported period and adapter compatibility checks pass
- **THEN** the endpoint returns deterministic metric rows with display metadata
- **THEN** returned metrics are derived from persisted portfolio and market history only

#### Scenario: Adapter compatibility mismatch is rejected explicitly
- **WHEN** required QuantStats call paths are unavailable for the pinned runtime version
- **THEN** the endpoint returns explicit failure with factual compatibility detail
- **THEN** the service does not fabricate substitute metric values

### Requirement: Benchmark-relative quant metrics SHALL be optional and explicit
The quant metrics endpoint SHALL treat benchmark-relative metrics as optional outputs that are emitted only when compatible benchmark series and adapter call paths are available; absence SHALL be explicit and SHALL NOT invalidate core quant metric computation.

#### Scenario: Benchmark-relative metrics omitted without blocking core metrics
- **WHEN** benchmark-relative metrics cannot be computed safely for the selected period
- **THEN** the endpoint still returns supported non-benchmark quant metrics
- **THEN** the payload includes explicit benchmark-context metadata indicating omission reason/scope

### Requirement: Quant metrics endpoint SHALL remain read-only and deterministic
Quant metric requests SHALL remain read-only over canonical, ledger, lot, and market-data state and SHALL preserve deterministic ordering and period semantics.

#### Scenario: Quant metrics request produces deterministic read-only output
- **WHEN** the same persisted state and period are requested repeatedly
- **THEN** metric ordering and value semantics remain deterministic for the same inputs
- **THEN** the request path performs no database mutation side effects

### Requirement: Portfolio quant report contracts SHALL remain route-agnostic for dedicated analytical surfaces
The portfolio analytics API SHALL expose quant report generation and retrieval contracts that are consumable from any approved workspace route surface, including dedicated `Quant/Reports`, without requiring Home-specific request context.

#### Scenario: Quant report endpoints succeed without Home-route coupling
- **WHEN** a client requests quant report generation or retrieval from a dedicated analytical workflow
- **THEN** the API validates scope inputs using contract-defined request fields only
- **THEN** the API does not require Home-route-only context flags or implied UI state to process the request

### Requirement: Portfolio quant report responses SHALL expose explicit workflow metadata for promoted UX
The portfolio analytics API SHALL include explicit report workflow metadata required by promoted Quant/Reports UX, including deterministic scope identity and artifact lifecycle status.

#### Scenario: Report payload provides deterministic scope and lifecycle context
- **WHEN** a report generation or retrieval request returns successfully
- **THEN** the payload includes explicit scope identity and artifact lifecycle metadata needed for route-level rendering
- **THEN** frontend clients do not infer report state from missing fields or implicit defaults

### Requirement: Portfolio analytics API SHALL expose risk-evolution chart datasets
The portfolio analytics API SHALL provide chart-ready risk-evolution datasets for approved scopes and periods, including drawdown path and rolling estimator series.

#### Scenario: Risk-evolution datasets return drawdown and rolling series
- **WHEN** a client requests risk-evolution analytics for a supported scope and period
- **THEN** the API returns ordered drawdown-path points and rolling-series points with explicit timestamps
- **THEN** the payload includes methodology metadata required for frontend interpretation

### Requirement: Portfolio analytics API SHALL expose deterministic return-distribution datasets
The portfolio analytics API SHALL provide deterministic return-distribution bucket outputs from persisted return history for approved scope and period inputs.

#### Scenario: Return-distribution buckets are deterministic for equivalent input state
- **WHEN** the same persisted state, scope, period, and bucket policy are requested repeatedly
- **THEN** the API returns the same bucket boundaries and counts
- **THEN** the response includes bucket-policy metadata used for chart rendering

### Requirement: Scope semantics SHALL remain explicit and consistent across chart analytics contracts
The API SHALL enforce explicit scope semantics for risk-evolution and return-distribution datasets using the existing `scope` and `instrument_symbol` contract posture.

#### Scenario: Missing symbol for instrument scope is rejected explicitly
- **WHEN** a client requests scope `instrument_symbol` without a valid `instrument_symbol` parameter
- **THEN** the API returns explicit client-facing validation failure
- **THEN** the service does not infer or default symbol scope implicitly

### Requirement: Portfolio analytics contracts SHALL provide investment P&L decomposition semantics
Portfolio analytics contracts SHALL support investment P&L decomposition context (realized, unrealized, period change, total return context) for dashboard storytelling without mixing business-income-statement semantics.

#### Scenario: P&L decomposition fields are explicit and portfolio-scoped
- **WHEN** a client requests portfolio analytics summary/decomposition data
- **THEN** response fields and metadata distinguish realized and unrealized components plus period-level movement context
- **THEN** contracts remain aligned to portfolio investment semantics and do not introduce company-income-statement line items

### Requirement: Portfolio analytics API SHALL expose deterministic health-synthesis outputs
The API SHALL expose a deterministic portfolio-health synthesis payload that aggregates approved KPI groups into explicit pillar scores and a bounded aggregate health label.

#### Scenario: Health synthesis payload includes score, label, pillars, and drivers
- **WHEN** a client requests portfolio health interpretation for a supported scope/period
- **THEN** the response includes `health_score`, `health_label`, `profile_posture`, and fixed-order pillar outputs
- **THEN** the response includes deterministic key drivers and caveat metadata describing any missing/omitted context

### Requirement: Health synthesis SHALL support profile posture weighting explicitly
The API SHALL support posture-specific weighting (`conservative`, `balanced`, `aggressive`) and SHALL expose effective weights used for score construction.

#### Scenario: Profile posture selection changes score deterministically
- **WHEN** equivalent data is requested with different profile posture values
- **THEN** score and label outputs follow the configured posture weighting deterministically
- **THEN** response metadata exposes effective weights and applied threshold policy version

### Requirement: Portfolio analytics API SHALL expose explicit exposure decomposition datasets
The API SHALL provide exposure decomposition payloads for supported dimensions (`asset_class`, `sector`, `currency`, `country`) with deterministic aggregation and explicit as-of metadata.

#### Scenario: Exposure decomposition returns deterministic grouped outputs
- **WHEN** a client requests exposure decomposition for a supported dimension and scope
- **THEN** the response returns grouped weights and value totals with stable ordering
- **THEN** the payload includes evaluation timestamps and scope metadata for interpretation

#### Scenario: Unsupported decomposition dimension is rejected
- **WHEN** a client requests an unsupported decomposition dimension
- **THEN** the API returns explicit validation failure
- **THEN** no implicit fallback dimension is applied

### Requirement: Portfolio analytics API SHALL expose contribution-to-risk datasets
The API SHALL provide per-symbol contribution-to-risk metrics for supported periods and scopes, with methodology metadata required for chart interpretation.

#### Scenario: Contribution-to-risk payload is returned for supported scope
- **WHEN** contribution-to-risk inputs satisfy minimum history requirements
- **THEN** the response includes per-symbol contribution rows and concentration context
- **THEN** the response includes methodology metadata and as-of references

#### Scenario: Contribution-to-risk inputs are insufficient
- **WHEN** required return history coverage is insufficient for requested scope/period
- **THEN** the API returns explicit unavailable or rejected state with factual coverage reason
- **THEN** the service does not emit synthetic contribution-to-risk values

### Requirement: Portfolio analytics API SHALL expose bounded correlation matrix contracts
The API SHALL provide bounded correlation matrix outputs for supported scopes with explicit minimum-history and symbol-universe policies.

#### Scenario: Correlation matrix is available
- **WHEN** requested scope has sufficient aligned return history for selected symbols
- **THEN** the response includes matrix cells and symbol ordering metadata
- **THEN** the payload includes guardrail metadata for low-sample or partially missing cells

#### Scenario: Correlation matrix cannot be computed safely
- **WHEN** symbol alignment or sample size fails minimum requirements
- **THEN** the API returns explicit failure/unavailable metadata
- **THEN** the service does not backfill guessed correlation values
