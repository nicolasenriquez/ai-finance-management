## ADDED Requirements

### Requirement: Compact first-viewport data SHALL be orchestrated at route level
The frontend SHALL orchestrate first-viewport server-state dependencies at route level for `/portfolio/home`, `/portfolio/analytics`, `/portfolio/risk`, and `/portfolio/signals` instead of fragmenting critical loads across deep widget trees.

#### Scenario: Route-level orchestration resolves primary modules deterministically
- **WHEN** a compact route is opened with valid backend availability
- **THEN** primary module requests are triggered from route-level orchestration boundaries
- **THEN** route-level loading and retry behavior remains deterministic and inspectable

### Requirement: Independent primary-module requests SHALL execute without serial waterfalls
The frontend SHALL run independent first-viewport requests in parallel and SHALL avoid serial dependency chains unless one request requires data from another by contract.

#### Scenario: Independent requests are dispatched concurrently
- **WHEN** one route needs multiple independent datasets for its first viewport
- **THEN** the client dispatches those requests concurrently
- **THEN** one slow request does not block unrelated primary modules from reaching ready state

### Requirement: Compact routes SHALL lazy-load heavy secondary modules
The frontend SHALL lazy-load route bundles and heavy secondary modules with bounded fallback states so first-surface interpretation is not delayed by below-the-fold content.

#### Scenario: First-surface modules remain usable while secondary modules load
- **WHEN** a user lands on a compact route with deferred modules
- **THEN** route header, trust context, controls, and primary module remain interactive without waiting for deferred bundles
- **THEN** deferred modules render explicit loading placeholders until ready

### Requirement: Navigation transitions SHALL prefetch likely next-route data
The frontend SHALL prefetch likely next-route datasets for compact route transitions when user intent is detectable from navigation focus/hover or equivalent interaction signals.

#### Scenario: Intent-aware prefetch reduces route transition latency
- **WHEN** a user focuses or hovers a compact-route navigation target
- **THEN** the client prefetches bounded next-route datasets using typed query contracts
- **THEN** route transition renders with reduced loading overhead compared with cold navigation

### Requirement: Primary-module failures SHALL remain localized
The frontend SHALL isolate failures at module scope so one failing contract does not collapse route navigation or unrelated primary-route modules.

#### Scenario: One module fails while route shell remains operable
- **WHEN** one primary module request fails with a recoverable error
- **THEN** only the affected module renders factual error state and retry affordance
- **THEN** route shell navigation and unaffected modules remain available
