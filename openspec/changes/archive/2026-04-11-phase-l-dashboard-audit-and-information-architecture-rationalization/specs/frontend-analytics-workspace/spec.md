## ADDED Requirements

### Requirement: Primary analytical routes SHALL enforce one dominant first-viewport job with bounded module count
`Home`, `Analytics`, `Risk`, and `Quant/Reports` SHALL present one dominant first-viewport analytical job and SHALL keep first-surface primary modules within a bounded range (maximum 7) before progressive disclosure sections.

#### Scenario: Route opens with one dominant job and bounded primary modules
- **WHEN** a user lands on one primary analytical route
- **THEN** the first viewport exposes one clearly dominant analytical job panel
- **THEN** first-surface primary modules do not exceed the bounded module budget

### Requirement: Dashboard routes SHALL avoid duplicate visuals for the same analytical question
Routes SHALL not render multiple equal-priority visuals that answer the same question unless one is explicitly marked as secondary drill-down context.

#### Scenario: Duplicate insight visuals are merged or demoted
- **WHEN** a route contains two visuals that represent the same analytical conclusion
- **THEN** one visual is retained as canonical and the other is merged, moved, or demoted to drill-down context
- **THEN** users are not forced to parse duplicate charts in the primary route flow

### Requirement: Dashboard IA SHALL map route content to four monitoring lenses
Workspace content SHALL be mapped and labeled by monitoring lens (`Overview`, `Holdings`, `Performance`, `Cash/Transactions`) to clarify where users should answer each business question.

#### Scenario: Route modules expose explicit lens alignment
- **WHEN** route-level modules are rendered
- **THEN** module grouping and copy indicate the intended monitoring lens
- **THEN** cross-lens modules are linked as drill-down navigation rather than competing first-surface blocks

### Requirement: High-density analytical routes SHALL use progressive disclosure for advanced modules
Advanced diagnostics SHALL be presented through explicit secondary sections, toggles, or linked drill-downs instead of loading all advanced modules at equal priority on initial render.

#### Scenario: Advanced diagnostics remain accessible but de-emphasized initially
- **WHEN** a route includes advanced diagnostics (for example deep risk labs or model-governance tables)
- **THEN** those diagnostics are reachable through explicit progressive disclosure affordances
- **THEN** initial route scan remains focused on primary interpretation outcomes
