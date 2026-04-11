## ADDED Requirements

### Requirement: Opportunity scan SHALL honor explicit DCA policy controls from request contracts
The system SHALL apply `opportunity_strategy_profile`, `double_down_threshold_pct`, and `double_down_multiplier` values from the validated chat request when `operation=opportunity_scan`, instead of relying on hidden frontend defaults.

#### Scenario: Valid DCA controls are applied to deterministic classification
- **WHEN** an opportunity-scan request supplies supported profile and in-range threshold/multiplier values
- **THEN** deterministic opportunity classification uses those values for action-state and action-multiplier outcomes
- **THEN** request processing remains bounded by existing read-only and tool-budget limits

#### Scenario: Invalid DCA controls fail fast
- **WHEN** an opportunity-scan request includes unsupported profile IDs or out-of-range threshold/multiplier values
- **THEN** the request is rejected with explicit blocked/error semantics and stable reason metadata
- **THEN** no deterministic ranking or AI narration is generated from invalid policy inputs

### Requirement: Double-down classification SHALL require full evaluable 52-week history
The system SHALL not classify a candidate as `double_down_candidate` unless 52-week history coverage is present and sufficient to evaluate drawdown-threshold policy deterministically.

#### Scenario: Candidate lacks full 52-week history
- **WHEN** a candidate row has fewer than 252 history points or otherwise cannot evaluate 52-week drawdown semantics
- **THEN** the candidate is not classified as `double_down_candidate`
- **THEN** action reasoning includes explicit insufficiency metadata for downstream inspection

#### Scenario: Candidate has full 52-week history and meets policy threshold
- **WHEN** a candidate row has evaluable 52-week context and satisfies configured DCA threshold policy
- **THEN** deterministic action-state classification may assign `double_down_candidate`
- **THEN** returned action multiplier reflects the validated DCA control value
