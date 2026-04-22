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

### Requirement: Opportunity responses SHALL use one SOT DCA assessment envelope
The system SHALL frame opportunity outputs using one stable DCA assessment envelope that includes baseline cadence discipline, double-down eligibility, fundamentals proxy posture, concentration/risk implications, and next-check guidance.

#### Scenario: Deterministic opportunity output maps to SOT envelope sections
- **WHEN** an opportunity-scan request completes successfully
- **THEN** response narration and prompt guidance are aligned to deterministic candidate output and reason codes
- **THEN** the response explicitly distinguishes deterministic rule outcomes from interpretive commentary

#### Scenario: Fundamentals evidence remains proxy-scoped
- **WHEN** fundamentals assessment is derived from deterministic proxy metrics
- **THEN** the response includes explicit caveat language that proxy checks do not replace manual fundamental verification
- **THEN** no section implies guaranteed return or execution guidance

### Requirement: SOT risk gating SHALL prevent optimistic escalation under insufficient context
The system SHALL not escalate to `double_down_candidate` when critical gating context fails or remains insufficient, even if superficial drawdown inputs appear attractive.

#### Scenario: Threshold appears met but gating context is insufficient
- **WHEN** drawdown threshold is met but 52-week eligibility or fundamentals-proxy gates are not passed deterministically
- **THEN** action-state remains non-escalated (`baseline_dca`, `watchlist`, or `hold_off`)
- **THEN** action reasoning includes explicit insufficiency/failure metadata for downstream inspection

#### Scenario: Insufficient context is surfaced instead of inferred
- **WHEN** available data cannot support full DCA SOT interpretation
- **THEN** the response includes explicit insufficiency caveats and follow-up checks
- **THEN** no fabricated personal-finance assumptions are introduced
