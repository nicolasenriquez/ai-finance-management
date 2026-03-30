## ADDED Requirements

### Requirement: Home route SHALL isolate optional quant/report failures from core context
The frontend SHALL render section-scoped loading/empty/error states for optional quant and report modules so that core Home context (summary/trend/hierarchy) remains available when optional modules fail.

#### Scenario: Quant section failure does not replace full Home with page-level error
- **WHEN** Home summary/trend/hierarchy data is available but quant metrics or report metadata requests fail
- **THEN** the Home page still renders core context modules
- **THEN** the quant/report section renders explicit factual error state with retry affordance

### Requirement: Quant and risk module placement SHALL remain explicit and consistent
The frontend SHALL keep drawdown and risk-interpreted metrics in risk-context surfaces while allowing bounded quant previews on Home and dedicated quant/report routes, with explicit scope labels.

#### Scenario: User can distinguish preview metrics from risk-context metrics
- **WHEN** Home and Risk routes are rendered
- **THEN** Home quant cards are labeled as preview or supplemental context
- **THEN** risk-context cards/charts display methodology/scope labels for interpretation

### Requirement: Quant report actions SHALL expose explicit lifecycle and omission context
The frontend SHALL expose deterministic report-generation and report-retrieval action states, and SHALL surface explicit benchmark omission context when optional benchmark-relative quant metrics are unavailable.

#### Scenario: Report action flow remains explicit and section-scoped
- **WHEN** a user generates a quant report from Home quant/report controls
- **THEN** the UI renders explicit loading, error, and ready states for generation and retrieval
- **THEN** report action failures do not replace core Home context with a page-level failure state

#### Scenario: Optional benchmark metric omissions are visible
- **WHEN** quant response payload includes benchmark omission metadata
- **THEN** the UI renders omission reason and omitted metric identifiers explicitly in quant/report context
- **THEN** absence of optional benchmark metrics is not presented as successful metric computation

### Requirement: Hierarchy table interactions SHALL remain deterministic and accessible after visual updates
Hierarchy table visual refinements SHALL preserve deterministic expand/collapse, grouping controls, and keyboard operability while maintaining explicit numeric/date formatting semantics.

#### Scenario: Hierarchy controls remain deterministic after style updates
- **WHEN** users toggle group or asset expansion and pivot controls in the hierarchy table
- **THEN** row expansion state transitions remain deterministic and reversible
- **THEN** keyboard focus and control labeling remain explicit and operable
