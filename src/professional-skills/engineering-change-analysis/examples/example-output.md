# Example Output

## Problem and Desired Behavior

Reject an API request with the existing stable error when the new field is
invalid while preserving old-client behavior.

## Acceptance and Non-goals

Valid requests retain their result, invalid values receive the stable error,
boundary values follow the schema, and forbidden invalid persistence never
occurs. Changing unrelated request validation is a non-goal.

## Ownership and Invariants

The API schema owns the wire contract; the service owns the business rule. The
database record must never contain an invalid field value.

## Placement and Reuse

Source evidence proves that the existing service-boundary validator owns this
rule and is reused; no structural choice or Specialist input remains.

## Contract / Data / Failure Impact

The API schema, validation, consumer error handling, tests, and public
documentation are affected. The database record must never contain the invalid
value; the stable error remains the failure contract.

## Validation Strategy

Run the focused service contract tests for valid, invalid, minimum/maximum, and
persistence-forbidden cases after the latest edit. Record consumer compatibility
and any unavailable external-consumer proof.

## Risks and Rollback

Unknown external consumers remain explicit. Rollback would revert the validator
and schema together so mixed contract behavior is not left behind.

## First Executable Slice

Task ID: example-api-validation-001
Goal: enforce the accepted field rule at the owning service boundary
Owner: service validation owner
Inputs: current Engineering Brief, schema, validator, focused tests
Allowed Read Scope: schema, validator, direct consumers, and focused tests
Allowed Write Scope: owning validator and focused regression tests
Non-goals: unrelated request validation or consumer cleanup
Dependencies: none
Expected Output: accepted validation behavior and regression evidence
Acceptance: valid, invalid, boundary, and forbidden outcomes above
Verification: focused service contract tests after the latest material edit
Evidence Requirements: current red/green proof and same-pattern scan result
Parallel Safety: no parallel writes
Workspace Requirement: shared; serialize writes
Integration Owner: service validation owner
Review Boundary: independent review of the validator, schema, focused tests, and consumer-compatibility evidence
Stop Conditions: ownership, contract, or write scope conflicts with this Brief

## Task Dependencies

The First Executable Slice has no dependency. Consumer documentation is a
remaining task only if its existing source proves a required contract update.

## Integration Boundary

The service validation owner integrates schema and validator behavior.

## Review Boundary

One independent implementation review covers the latest diff, every changed
file, contract behavior, and consumer-compatibility evidence.

## Evidence Gaps and Proof Limits

Unknown external consumers are a proof limit and do not authorize unrelated
consumer edits.
