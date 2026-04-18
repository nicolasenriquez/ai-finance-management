## ADDED Requirements

### Requirement: Workspace shell SHALL support route-aware density profiles
The frontend SHALL provide route-aware shell density profiles that allow dashboard routes to opt into `expanded`, `standard`, or `compact` shell presentation while preserving persistent navigation and global actions.

#### Scenario: Dense routes reduce chrome without losing orientation
- **WHEN** a high-density analytical route loads
- **THEN** the shell can render a lower-noise density profile that preserves navigation, active-route state, and core actions
- **THEN** non-critical chrome does not outrank the route's dominant analytical surface in the first viewport

### Requirement: Workspace shell SHALL present freshness and provenance as support context
The frontend SHALL present freshness, provenance, and trust metadata in a compact support layer adjacent to route context rather than as competing hero-level chrome.

#### Scenario: Trust context remains available without dominating the route
- **WHEN** a dashboard route renders freshness or provenance metadata
- **THEN** that information is visible in a stable support rail or route header treatment
- **THEN** the metadata reinforces trust without visually displacing the route's primary job or hero insight

### Requirement: Workspace shell SHALL make lens orientation explicit
The frontend SHALL expose the active dashboard lens through stable shell treatments such as chips, labels, or grouped navigation semantics so users understand the workspace mode immediately after navigation.

#### Scenario: Active lens is visually explicit across route changes
- **WHEN** a user navigates between `Overview`, `Holdings`, `Performance`, and `Cash/Transactions`
- **THEN** the shell highlights the current lens deterministically
- **THEN** the route header and navigation semantics reinforce the same active lens without contradictory labels
