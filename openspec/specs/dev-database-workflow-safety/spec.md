# dev-database-workflow-safety Specification

## Purpose
TBD - created by archiving change resolve-yfinance-live-provider-blockers. Update Purpose after archive.
## Requirements
### Requirement: Local workflow SHALL isolate runtime and test database targets
The system SHALL require explicit separation between runtime `DATABASE_URL` and `TEST_DATABASE_URL` in local command workflows so application runtime and test execution cannot silently mutate the same database.

#### Scenario: Runtime workflow resolves to test database target
- **WHEN** a local runtime workflow (for example `just dev`) resolves `DATABASE_URL` to a database that matches test URL input or a `_test` database name
- **THEN** the command fails explicitly before starting runtime services
- **THEN** the failure message tells the operator to configure separate runtime and test database URLs

#### Scenario: Test workflow does not define isolated test database
- **WHEN** test workflows (`just test`, `just test-integration`) run without a resolvable `TEST_DATABASE_URL` or with `TEST_DATABASE_URL` equal to `DATABASE_URL`
- **THEN** the workflow fails explicitly before migrations or pytest execution
- **THEN** no test-stage schema migration or test run is executed against the runtime database target

### Requirement: Test-oriented workflows SHALL run migrations and tests against test database URL
The system SHALL execute test migrations and pytest commands with test database URL context rather than runtime database URL context.

#### Scenario: Integration workflow prepares schema
- **WHEN** `just test-integration` is invoked
- **THEN** schema upgrade runs against `TEST_DATABASE_URL`
- **THEN** integration tests execute with `DATABASE_URL` bound to the test database URL for that command context

#### Scenario: Non-integration test workflow executes
- **WHEN** `just test` is invoked
- **THEN** non-integration pytest runs with `DATABASE_URL` bound to the test database URL for that command context
- **THEN** runtime database URL remains untouched by the test command execution context
