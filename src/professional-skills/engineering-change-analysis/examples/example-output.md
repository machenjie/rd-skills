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

## Implementation and Coordination

Update the existing service validator and focused regression tests. Inspect the
schema and direct consumers as needed; keep edits within the validator and test
owner. Consumer documentation needs a separate change only if current source
establishes a changed public contract. The service owner integrates schema and
validator behavior. Independent review is useful if consumer compatibility
cannot be established through contract tests and source inspection.

## Evidence Gaps and Proof Limits

Unknown external consumers are a proof limit and do not authorize unrelated
consumer edits.
