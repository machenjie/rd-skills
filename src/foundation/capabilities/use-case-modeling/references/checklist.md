# Use Case Modeling Checklist

- Name the use case and primary actor.
- State actor goal in product terms.
- Define preconditions that must already be true.
- Define trigger that starts the use case.
- Define main path as behavior, not implementation.
- Define alternate paths that still reach an acceptable outcome.
- Define failure paths and recovery or exit behavior.
- Define postconditions and durable state changes.
- Identify business rules, permissions, and events touched.
- Map use case to acceptance or test evidence.

## Source Confirmation

- Treat project memory, generated notes, repository graph proximity, and execution trajectory as leads, not proof.
- Confirm existing behavior in current source, tests, docs, schemas, registry entries, or stakeholder-owned artifacts before reusing a use case.
- Record accepted and rejected evidence with freshness: path, date or command, and what changed since the evidence was produced.
- Mark unavailable production behavior, external-system contracts, or stakeholder decisions as evidence limits with an owner.

## Guarantee Review

- Name the minimal guarantee when the actor goal is not achieved.
- Name the success guarantee when the actor goal is achieved.
- Assign owner and retry, compensation, or support recovery for each failure guarantee.
- Ensure every alternate and failure path leaves durable state, emitted events, and side effects in a defined condition.

## Handoff Check

- Hand off to `acceptance-standard-definition` when postconditions are ready to become criteria.
- Hand off to `scenario-decomposition` when path coverage is broader than one actor goal.
- Hand off to `state-machine-modeling` when lifecycle legality or terminal states need depth.
- Hand off to `permission-boundary-modeling` when actor/resource/action/scope or denied behavior is material.
- Hand off to `quality-test-gate` when acceptance/test evidence, validator choice, command freshness, or residual risk must be planned before implementation.
