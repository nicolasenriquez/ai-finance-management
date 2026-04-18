## ADDED Requirements

### Requirement: Primary dashboard routes SHALL follow an executive-operator first viewport
The frontend SHALL compose `Overview/Home`, `Holdings`, `Performance`, and `Cash/Transactions` routes so the first viewport contains one dominant job panel, one hero insight, and a bounded set of supporting modules before advanced diagnostics.

#### Scenario: Route first viewport answers the dominant question immediately
- **WHEN** a user opens a primary dashboard route
- **THEN** the first viewport communicates the route's dominant analytical job without relying on multiple competing hero modules
- **THEN** supporting modules are limited to the smallest set needed to orient the next drill-down decision

### Requirement: Dashboard route sequencing SHALL progress from overview to drill-down to evidence
The frontend SHALL order first-surface and secondary dashboard modules using an `overview -> drill-down -> evidence` sequence so users can move from summary interpretation to supporting detail deterministically.

#### Scenario: Dashboard surfaces provide an interpretable narrative arc
- **WHEN** a route renders summary metrics, charts, and deeper tables
- **THEN** users encounter a summary interpretation layer before deeper breakdowns
- **THEN** evidence surfaces such as detailed ledgers, diagnostics, or supporting tables remain reachable without displacing the summary layer

### Requirement: Holdings and transactions routes SHALL use domain-appropriate operating layouts
The frontend SHALL render `Holdings` with a ledger-first structure and `Cash/Transactions` with an operating-console structure instead of reusing generic chart-grid composition.

#### Scenario: Route layout matches the domain question
- **WHEN** a user opens `Holdings` or `Cash/Transactions`
- **THEN** the dominant module is a sortable, scannable operating surface appropriate to the route domain
- **THEN** charts and summary cards act as supporting interpretation aids rather than replacing the route's primary ledger or console role

### Requirement: Promoted dashboard charts SHALL match the data relationship and benchmark context
The frontend SHALL use chart types that match the data relationship of the promoted insight and SHALL surface benchmark, target, or comparison context explicitly when an insight depends on relative interpretation.

#### Scenario: Chart form and comparison context are explicit
- **WHEN** a promoted dashboard chart is rendered for trend, ranking, distribution, or target comparison
- **THEN** the chart type matches that relationship and avoids decorative or misleading alternatives
- **THEN** any benchmark, target, or comparison frame needed for interpretation is visible in the module title, subtitle, legend, or adjacent utility copy
