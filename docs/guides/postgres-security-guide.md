# PostgreSQL Security Guide

## Purpose

This guide defines the practical PostgreSQL security posture for this repository.

Use it when:

- setting up a new environment
- exposing PostgreSQL beyond local-only development
- reviewing credentials, roles, or privileges
- deciding whether a database feature changes the security model

This guide complements:

- `docs/standards/postgres-standard.md` for repository rules
- `docs/standards/bandit-standard.md` for application-code security scanning
- `docs/guides/postgres-local-setup.md` for the local development workflow

## Current Assessment

Database security is only partially covered in the current documentation set.

What is already covered:

- application-code security scanning with Bandit
- fail-fast database behavior
- migration discipline
- extension governance

What was missing before this guide:

- PostgreSQL authentication posture
- role and privilege design
- network exposure rules
- TLS expectations
- credential handling guidance
- database-specific audit and review expectations

## Source Guidance

The PostgreSQL 7.0 security page is historical context only.

Why:

- the page itself states it is for an unsupported version
- the security model and recommended authentication methods have evolved substantially
- current repository guidance should anchor to PostgreSQL 18 behavior

Use current official PostgreSQL docs as authority, then use Tiger Data articles as practical secondary guidance.

## Security Model For This Repository

### Local development

Current local Compose setup is primarily for developer convenience. That means:

- some hardening measures can remain lighter in local-only usage
- those lighter defaults must not be mistaken for the correct posture for shared or remote environments

### Shared, remote, or production-like environments

If the database is reachable over a network or used by more than one operator, apply stricter controls immediately:

- least-privilege roles
- restricted `pg_hba.conf`
- TLS for client connections
- reviewed privileges on schemas and objects
- explicit credential rotation and auditability

## Authentication Guidance

### Preferred method

Use `scram-sha-256` for password authentication.

Why:

- current PostgreSQL documentation describes it as the most secure current password method
- `md5` is deprecated and scheduled for removal in a future PostgreSQL release

### Avoid or restrict

- `trust`: only acceptable for tightly scoped local development
- `password`: avoid on untrusted networks because it sends the password in clear text unless protected by TLS
- `md5`: legacy compatibility only

### `pg_hba.conf` rule posture

- keep entries as narrow as possible by database, user, address, and method
- prefer specific subnets or hosts over broad ranges
- review entry order carefully because first-match behavior matters
- use `hostssl` where remote SSL/TLS is required

## Network Exposure Guidance

- Keep `listen_addresses` narrow.
- Do not expose PostgreSQL publicly unless there is a clear operational reason.
- Prefer private-network or local-only access.
- Use firewalls and infrastructure-level controls in addition to PostgreSQL settings.

For this repository, the safest baseline is:

- local-only database exposure by default
- deliberate documentation and review before any broader exposure

## Role And Privilege Guidance

### Least privilege

- separate admin/setup responsibilities from application runtime responsibilities
- grant only what the application needs
- avoid superuser privileges for the app role

The local Docker baseline now reflects this split with:

- `postgres` for bootstrap and admin tasks
- `ai_finance_app` as the default runtime role

### Schema privileges

- review privileges on schema `public`
- in multi-role environments, revoke `CREATE` on schema `public` from `PUBLIC` unless there is a clear reason not to
- use explicit grants on schemas and objects

### Default privileges

When environments become shared, use `ALTER DEFAULT PRIVILEGES` intentionally so newly created objects do not inherit surprise access patterns.

## TLS And Encryption Guidance

### Data in transit

Use TLS for remote or shared-environment connections.

At minimum, document:

- whether TLS is required
- how certificates are provisioned
- how clients verify the server

### Data at rest

PostgreSQL security does not automatically solve all data-at-rest concerns.

If the project eventually stores secrets, tokens, or regulated data, decide explicitly whether encryption belongs:

- at the storage layer
- at the application layer
- in selected columns via cryptographic functions

Do not improvise this later in an ad hoc way.

## Credential Handling Guidance

- keep `DATABASE_URL` in environment configuration, not committed docs examples with real secrets
- do not reuse broad admin credentials for normal application runtime
- avoid logging full connection strings
- rotate passwords when access scope changes

## Logging, Auditing, And Review

### Minimum posture

- log database connection failures
- log privilege or migration failures clearly at the application layer
- keep enough context to trace destructive or schema-changing operations

### Review cadence

Review periodically:

- role memberships
- schema grants
- `pg_hba.conf` policy
- exposed network surfaces
- extension footprint

If audit requirements grow, evaluate more explicit database audit logging rather than assuming normal application logs are enough.

## Security-Sensitive PostgreSQL Features

These features are useful but should trigger explicit design review:

- `SECURITY DEFINER` functions and procedures
- row-level security
- security-boundary views
- cryptographic extensions such as `pgcrypto`
- authentication changes
- replication roles

### `SECURITY DEFINER`

Use only when the privilege boundary is intentional and reviewed.

Main risks:

- privilege escalation
- unsafe `search_path`
- hard-to-audit access paths

### Row-level security

Useful when multiple application actors must share tables with distinct row visibility rules.

Not currently required for this repository because the current MVP is single-user and local-first.

### `pgcrypto`

Potentially useful later for selective cryptographic operations, but it should not be added casually. Document the exact use case, key handling, and threat model first.

## Recommended Documentation Structure

The current repo should keep database security documentation in two places:

1. `docs/standards/postgres-standard.md`
2. `docs/guides/postgres-security-guide.md`

Why this split works:

- the standard keeps durable security rules close to schema and migration rules
- the guide gives operators and future contributors an actionable setup and review playbook

## What Not To Do

- do not use PostgreSQL 7.0 documentation as normative security guidance
- do not assume local-dev defaults are safe for shared environments
- do not run the app as superuser
- do not keep broad `trust` rules after initial setup
- do not rely on default `PUBLIC` privileges without checking them
- do not introduce `SECURITY DEFINER` or row-level security without explicit design review

## References

- PostgreSQL 7.0 security page, historical only: https://www.postgresql.org/docs/7.0/security.htm
- PostgreSQL 18 client authentication: https://www.postgresql.org/docs/18/client-authentication.html
- PostgreSQL 18 `pg_hba.conf`: https://www.postgresql.org/docs/18/auth-pg-hba-conf.html
- PostgreSQL 18 password authentication: https://www.postgresql.org/docs/18/auth-password.html
- PostgreSQL 18 roles: https://www.postgresql.org/docs/18/user-manag.html
- PostgreSQL 18 `GRANT`: https://www.postgresql.org/docs/18/sql-grant.html
- PostgreSQL 18 default privileges: https://www.postgresql.org/docs/18/sql-alterdefaultprivileges.html
- PostgreSQL 18 schemas and privileges: https://www.postgresql.org/docs/18/ddl-schemas.html
- PostgreSQL 18 function security: https://www.postgresql.org/docs/18/perm-functions.html
- Tiger Data PostgreSQL security guide: https://www.tigerdata.com/learn/guide-to-postgresql-security
- Tiger Data developer guide: https://dev.to/tigerdata/postgresql-security-best-practices-a-developers-guide-47f7
