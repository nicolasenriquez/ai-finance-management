## ADDED Requirements

### Requirement: Opportunities label SHALL remain mapped to `/portfolio/signals`
The compact shell SHALL preserve `/portfolio/signals` as the canonical tactical route while presenting `Opportunities` as the visible navigation label.

#### Scenario: Route slug and user-facing label stay intentionally distinct
- **WHEN** a user navigates to the tactical route from shell navigation
- **THEN** the URL resolves to `/portfolio/signals`
- **THEN** the visible navigation and route framing label render as `Opportunities`

### Requirement: Opportunities ranking SHALL be derived from live contract-backed context
The opportunities workspace SHALL derive ranking, trend, and watchlist context from typed summary and market contracts instead of static route-local constants.

#### Scenario: Opportunity ranking reflects current holdings and market context
- **WHEN** opportunities route data resolves successfully
- **THEN** ranking and watchlist modules are computed from current contract-backed payloads
- **THEN** static hardcoded candidate lists are not used as first-surface evidence

### Requirement: Opportunities modules SHALL expose deterministic reason-code framing
The opportunities workspace SHALL render deterministic reason-code and action-state framing for tactical candidates, including freshness and confidence context when available.

#### Scenario: Candidate rows include explicit interpretation cues
- **WHEN** one candidate is rendered in ranking or watchlist modules
- **THEN** the row shows deterministic reason-code/action-state cues
- **THEN** freshness and confidence context is visible when provided by source contracts

### Requirement: Opportunities route SHALL preserve factual async-state copy
The opportunities route SHALL render factual module copy for loading, empty, unavailable, and error states, and SHALL avoid generic ambiguous `Unavailable` first-surface messaging.

#### Scenario: Missing tactical data communicates factual next action
- **WHEN** one tactical module cannot render due to missing or stale contract data
- **THEN** the module displays factual unavailable or error copy with reason and retry/next-step guidance
- **THEN** users can distinguish missing data from contract-disabled behavior

### Requirement: Opportunities route SHALL preserve secondary tactical posture
The opportunities workspace SHALL remain secondary to executive and risk routes and SHALL not redefine the product as an execution terminal.

#### Scenario: Tactical route framing preserves portfolio-first hierarchy
- **WHEN** the opportunities route is rendered
- **THEN** route framing and module ordering reinforce review-and-monitor posture
- **THEN** the UI does not imply direct order execution or intraday terminal workflows
