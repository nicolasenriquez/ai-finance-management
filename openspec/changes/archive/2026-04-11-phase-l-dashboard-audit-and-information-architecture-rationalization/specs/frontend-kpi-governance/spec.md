## ADDED Requirements

### Requirement: KPI and widget governance SHALL encode business-question ownership
Promoted KPI and dashboard widget governance SHALL include the business question each element answers and the portfolio decision it enables.

#### Scenario: Governance row documents question-to-decision traceability
- **WHEN** a KPI or primary widget is promoted in one workspace route
- **THEN** governance metadata records the business question answered by that element
- **THEN** governance metadata records one portfolio decision category supported by that element

### Requirement: Governance SHALL require benchmark/comparison context for promoted performance signals
Promoted performance and risk signals SHALL document explicit comparison context (benchmark, prior period, target band, or concentration baseline) before they are treated as complete.

#### Scenario: Promoted metric includes comparison framing
- **WHEN** a metric is promoted for executive interpretation on `Home`, `Analytics`, `Risk`, or `Quant/Reports`
- **THEN** governance defines the required comparison baseline used in route copy or explainability
- **THEN** metrics without comparison framing are not treated as fully promoted

### Requirement: Dashboard simplification decisions SHALL be traceable in governance artifacts
When widgets are merged, moved, or removed, governance artifacts SHALL capture severity, rationale, and destination behavior for future audits.

#### Scenario: Widget move or removal remains auditable
- **WHEN** a route module is merged, moved to another lens, or removed
- **THEN** governance artifacts record severity and rationale for the decision
- **THEN** destination route or replacement behavior is documented in the same change evidence
