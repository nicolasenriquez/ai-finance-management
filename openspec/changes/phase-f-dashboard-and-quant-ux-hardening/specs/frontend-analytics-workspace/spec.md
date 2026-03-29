## ADDED Requirements

### Requirement: Frontend analytics workspace SHALL expose a dedicated Quant/Reports surface
The frontend SHALL provide a dedicated `Quant/Reports` workspace surface for report generation and advanced quant diagnostics so HTML report workflows are not buried in the Home route.

#### Scenario: Quant report workflow starts from dedicated surface
- **WHEN** a user needs to generate or retrieve a Quant report
- **THEN** the workflow entry is available from a dedicated `Quant/Reports` workspace surface
- **THEN** Home remains focused on executive snapshot context and does not serve as the primary report-generation surface

### Requirement: Workspace chart modules SHALL follow one shared composition contract
The frontend SHALL enforce one chart composition contract across Home, Analytics, and Risk routes, including responsive container sizing, consistent panel spacing, and shared chart header semantics.

#### Scenario: Chart layout tokens are consistent across routes
- **WHEN** chart modules render in Home, Analytics, and Risk
- **THEN** they use the same spacing and container sizing tokens defined by shared workspace primitives
- **THEN** route-specific chart modules do not introduce unreviewed one-off sizing or spacing behavior

## MODIFIED Requirements

### Requirement: Home route SHALL foreground first-viewport portfolio context
The Home route SHALL render first-viewport trust context with executive KPI summary cards and at least one trend visualization backed by typed analytics responses, while limiting the route to preview-oriented analytics rather than full report workflow ownership.

#### Scenario: Home route shows executive snapshot without owning full report workflow
- **WHEN** Home data loads successfully
- **THEN** the first viewport includes portfolio-level KPI cards and one trend chart
- **THEN** the screen displays data freshness/provenance context and does not rely on implied values
- **THEN** report-generation actions are presented as navigation into dedicated analytical context instead of full workflow execution on Home
