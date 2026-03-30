## ADDED Requirements

### Requirement: Frontend analytics workspace SHALL preserve deterministic route-level trust cues
The frontend SHALL render route-level trust context (freshness, scope, provenance labels) on `Home`, `Analytics`, `Risk`, and `Transactions` so chart-heavy screens remain interpretable.

#### Scenario: Workspace routes show trust cues before detailed charts
- **WHEN** a user opens any analytics workspace route
- **THEN** the route displays freshness/scope/provenance cues near the page header region
- **THEN** users can identify data context before interpreting chart outputs

## MODIFIED Requirements

### Requirement: Frontend state handling SHALL remain explicit and deterministic for portfolio views
The frontend SHALL render explicit and user-comprehensible states for summary, lot-detail, and analytics-workspace routes (`Home`, `Analytics`, `Risk`, `Transactions`) across loading, empty, not-found, validation-error, and server-error paths, without silently substituting stale or inferred data.

#### Scenario: Analytics workspace routes report loading and empty states explicitly
- **WHEN** workspace route data is pending or returns no chartable rows
- **THEN** the UI shows dedicated loading and empty-state messaging for that route
- **THEN** it does not render synthetic chart traces as if supported data existed

#### Scenario: Error responses remain explicit and retry-capable on chart routes
- **WHEN** workspace route requests fail with `4xx` or `5xx`
- **THEN** the UI renders a factual error state with retry affordance
- **THEN** it does not mask failure as a successful empty visualization

#### Scenario: Risk methodology cues remain explicit in ready states
- **WHEN** risk routes render successful estimator responses
- **THEN** methodology cues (window, return basis, annualization basis, as-of context) are visible near estimator values
- **THEN** users are not required to infer hidden estimator defaults from chart appearance alone

### Requirement: Frontend release readiness SHALL include Core Web Vitals evidence for MVP views
The frontend SHALL capture and report Core Web Vitals evidence for core portfolio and analytics-workspace routes (`/portfolio`, `/portfolio/:symbol`, and newly introduced analytics workspace routes) and apply optimizations when thresholds are not met.

#### Scenario: CWV evidence is captured for summary, lot-detail, and workspace routes
- **WHEN** frontend hardening is validated for release
- **THEN** evidence includes LCP, INP, and CLS measurements for portfolio and analytics-workspace routes
- **THEN** results are recorded in project artifacts referenced by release documentation
