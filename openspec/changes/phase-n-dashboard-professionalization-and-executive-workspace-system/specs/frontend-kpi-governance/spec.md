## ADDED Requirements

### Requirement: Promoted dashboard insights SHALL declare decision framing and comparison context
The system SHALL document for each promoted dashboard insight the decision it enables, the primary benchmark or target context required for interpretation, and the evidence depth expected after first-view consumption.

#### Scenario: Promoted insight carries decision and comparison metadata
- **WHEN** a dashboard insight is promoted into a hero or first-surface module
- **THEN** its governance entry records the decision enabled and the benchmark, target, or comparison frame needed to interpret the value correctly
- **THEN** the governance entry records whether supporting evidence lives in a secondary chart, table, or advanced disclosure

### Requirement: KPI governance SHALL include chart-fit rationale for promoted visuals
The system SHALL record the approved chart form for promoted dashboard insights and the reason that chart fits the underlying data relationship, including any prohibited alternatives where misinterpretation risk is material.

#### Scenario: Chart selection is traceable and non-decorative
- **WHEN** a promoted KPI or insight is rendered using a chart
- **THEN** the governance artifact states the approved chart type and why it is appropriate for trend, ranking, distribution, contribution, or target comparison
- **THEN** visually attractive but misleading alternatives are not introduced without updating the governance rationale

### Requirement: KPI governance SHALL require accessible fallback evidence for promoted charts
The system SHALL define an accessible fallback or companion evidence path for promoted charts, such as direct labeling, summary text, or tabular evidence, when color, hover, or dense composition alone would hide meaning.

#### Scenario: Promoted chart meaning remains available without hover-only interpretation
- **WHEN** a promoted chart relies on color, compact density, or interaction to communicate a key insight
- **THEN** the governance entry specifies visible labels, summary text, or a companion table that preserves meaning accessibly
- **THEN** first-surface insights do not require hover-only interpretation to understand whether the reading is favorable, unfavorable, or inconclusive
