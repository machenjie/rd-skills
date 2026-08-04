# Use Case Modeling Decision Checklist

Load this checklist when drafting or reviewing one actor-goal use case. Do not load it for implementation planning, a cross-journey scenario inventory, or pure wording cleanup.

1. Name the use case, primary actor, secondary actors when material, and product goal.
2. State preconditions as facts already true and name the trigger that begins the case.
3. Express the main path as actor-visible behavior, not implementation steps.
4. Define alternate paths and the acceptable outcome each still achieves.
5. Define failure paths with safe exit, retry, compensation, or support recovery.
6. Name the minimum guarantee when the actor goal is not achieved.
7. Name the success guarantee when the actor goal is achieved.
8. Define durable postconditions, emitted events, external effects, and partial state for each applicable exit.
9. Identify business rules, actor/resource/action/scope permissions, and denied behavior with their owners.
10. Confirm existing behavior against current source, tests, contracts, schemas, or stakeholder-owned artifacts.
11. Record evidence as accepted, rejected, stale, or unknown with source and freshness.
12. State production, external-system, and stakeholder proof limits plus the residual owner.
13. When this use case changes a path or guarantee, map that change to acceptance criteria and test/validation evidence.
14. Route broader coverage to `scenario-decomposition`, lifecycle legality to `state-machine-modeling`, permissions to `permission-boundary-modeling`, criteria to `acceptance-standard-definition`, and executable proof to `quality-test-gate`.
