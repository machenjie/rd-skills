# Data API Contract Evidence Patterns

Use this reference when a contract change needs proof stronger than a local code review. Load only the rows needed for the changed contract surface.

## Evidence Map
- **Schema or DTO change:** capture old/new shape, compatibility class, generated artifact diff, consumer list, contract test command, exit code, and stale-client risk.
- **Endpoint request or response change:** prove wire examples, validation/error taxonomy, pagination/sort stability, idempotency semantics, and known-consumer behavior.
- **Migration or backfill:** prove expand/migrate/contract phase, forward command, rollback command, lock or table-size assumption, reconciliation artifact, and rollback time limit.
- **Generated SDK or client change:** prove generator command, checked-in diff, representative client compile/test result, versioning note, and release owner.
- **Deprecation or deletion:** prove telemetry/caller search, sunset date, replacement path, owner acknowledgement, cleanup issue, and rollback after deletion.

## Evidence Rules
- For executable or report-backed contract claims, record the validator, artifact, status, freshness, and exact claim; for manual review or owner evidence, record the procedure, result, scope, and proof limits.
- Every evidence item also states what it does not prove: unknown consumers, mobile/client lag, production data skew, version skew during rollout, or rollback under live traffic.
- Prefer existing OpenAPI/Protobuf/GraphQL generators, contract tests, migration validators, and repository consumer searches before adding new support machinery.
- Do not close a breaking change on schema diff alone; pair it with consumer readiness, versioning or EMC plan, and rollback evidence.
