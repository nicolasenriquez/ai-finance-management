## MODIFIED Requirements

### Requirement: Data sync operations SHALL provide a local `yfinance` refresh workflow
The system SHALL provide an operator-facing local workflow that triggers market-data refresh through the existing `yfinance` service seam for one resolved supported-universe scope mode (`core`, `100`, or `200`), preserving strict required-portfolio coverage while surfacing bounded partial-success evidence for approved non-portfolio blocker failures in `100/200`.

#### Scenario: Operator runs market refresh successfully with explicit or default scope
- **WHEN** the operator triggers market refresh with or without an explicit scope mode
- **THEN** the workflow invokes the market-data refresh orchestration for the resolved scope mode
- **THEN** the run result includes provider/source identity, selected scope mode, retry diagnostics, failed-symbol diagnostics, and refresh counters

#### Scenario: Market refresh blocks on required or unsupported failure
- **WHEN** provider fetch or normalization fails for a required-portfolio symbol or on an unsupported provider condition
- **THEN** the workflow reports explicit failure with actionable context
- **THEN** the workflow does not report bounded partial success for that run

### Requirement: Data sync operations SHALL provide a deterministic combined local sync workflow
The system SHALL provide a combined local sync workflow that runs bootstrap and market refresh in one deterministic sequence and propagates the selected or default refresh scope mode to the refresh stage.

#### Scenario: Combined sync succeeds with refresh diagnostics
- **WHEN** the operator triggers combined local sync with or without a refresh scope mode and both stages complete
- **THEN** bootstrap executes before market refresh
- **THEN** nested market-refresh evidence includes scope, retry diagnostics, failed-symbol diagnostics, and snapshot provenance needed for staged smoke comparison

#### Scenario: Combined sync fails in refresh stage
- **WHEN** bootstrap succeeds but refresh blocks on a required or unsupported provider failure
- **THEN** the combined workflow returns explicit failure state for the overall operation
- **THEN** the workflow does not hide the blocking refresh outcome behind bootstrap success
