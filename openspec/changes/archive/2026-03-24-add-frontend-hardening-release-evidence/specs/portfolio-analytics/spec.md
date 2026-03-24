## MODIFIED Requirements

### Requirement: Analytics APIs fail explicitly for unsupported symbol requests
The system SHALL reject unsupported or unknown lot-detail requests with explicit client-facing failure instead of ambiguous empty success when the requested instrument cannot be resolved safely, and frontend consumers SHALL map this response to a dedicated not-found UI state.

#### Scenario: Lot detail rejects unknown instrument symbol
- **WHEN** a client requests lot detail for an `instrument_symbol` that has no matching persisted ledger truth
- **THEN** the system returns an explicit client error
- **THEN** the response makes clear that the requested instrument was not found in the portfolio ledger
- **THEN** frontend consumers display a not-found state rather than an empty success table
