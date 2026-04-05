## ADDED Requirements

### Requirement: Each primary workspace route SHALL own one first-viewport analytical job
The frontend SHALL compose `Home`, `Analytics`, `Risk`, and `Quant/Reports` so each route communicates one dominant analytical purpose in the first viewport instead of presenting multiple competing primary modules.

#### Scenario: User can identify route purpose from first-viewport structure
- **WHEN** a user opens one primary workspace route
- **THEN** the route presents one dominant analytical surface and supporting utility copy that makes the route purpose immediately scannable
- **THEN** the first viewport does not depend on multiple equal-priority hero panels to explain the route

### Requirement: Workspace routes SHALL prioritize a `Core 10` interpretation layer before advanced diagnostics
The frontend SHALL promote a bounded `Core 10` metric layer ahead of advanced tables, distributions, or secondary diagnostics so users can interpret portfolio condition without scanning the entire route.

#### Scenario: Core metrics are visually and semantically distinct from advanced diagnostics
- **WHEN** a route renders promoted portfolio metrics
- **THEN** the UI distinguishes `Core 10` metrics from advanced diagnostics through stable sectioning and ordering
- **THEN** advanced modules remain available without displacing the primary interpretation layer

### Requirement: Workspace SHALL surface personal-finance operating insights explicitly
The frontend SHALL surface personal-finance operating insights such as allocation drift, dividend income, goal progress, forecast confidence, and freshness or trust context where approved typed data is available.

#### Scenario: Personal-finance insight module renders or fails explicitly
- **WHEN** a route has approved data for one personal-finance operating insight
- **THEN** the UI renders that insight with scope, freshness, and interpretation context
- **THEN** if the required data is unavailable, the route shows an explicit unavailable state instead of omitting the insight silently

### Requirement: Workspace routes SHALL use one shared trust-state and utility-copy system
The frontend SHALL present `loading`, `ready`, `stale`, `unavailable`, `blocked`, and `error` states with shared utility-copy semantics across analytical routes.

#### Scenario: Equivalent lifecycle states map to consistent route behavior
- **WHEN** two workspace routes receive the same lifecycle condition such as `stale` or `unavailable`
- **THEN** each route presents the condition using the same state vocabulary and trust-oriented copy pattern
- **THEN** users do not need route-specific tribal knowledge to interpret whether the data is current, missing, or blocked
