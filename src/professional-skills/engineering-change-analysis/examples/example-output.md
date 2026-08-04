# Example Output

## Problem and Acceptance

Reject an API request with the existing stable error when the new field is
invalid; preserve old-client behavior. Negative, compatibility, and recovery
paths map to contract and service tests.

## Ownership and Invariants

The API schema owns the wire contract; the service owns the business rule. The
database record must never contain an invalid field value.

## Placement, Contract, Data, and Failure Design

Source evidence identifies the existing service-boundary validator as the
candidate placement. Affected surfaces are the schema, validation, consumer
error handling, tests, and public documentation.

## Non-Authoritative Slice Hypothesis

After the Engineering Brief is accepted, one candidate boundary could cover the
failing service-level regression test and the owning validator, with the
targeted service test as evidence. This hypothesis is non-authoritative and
non-dispatchable; it does not authorize implementation or review dispatch.

## Candidate Task Boundaries and Scheduling Handoff

The schema and validator form one candidate task boundary. Consumer
compatibility and public documentation remain separate candidates when their
owners or verification differ. After the Engineering Brief is accepted, hand
these candidates, DAG-trigger evidence, and unresolved scheduling constraints
to `task-dag-planner`; it independently selects the First Executable Slice and
solely emits any authoritative Task DAG or Task Contract v2.

## Risks and Rollback

Unknown external consumers remain explicit. Rollback would revert the validator
and schema together so mixed contract behavior is not left behind.
