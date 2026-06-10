Selected stage: implementation-planning.
Selected professional skill: backend-change-builder.
Selected capabilities: transaction-consistency, service-business-logic, logging-error-handling, data-migration-design.

Hidden risks: inconsistent account and billing state; event emitted without durable state or compensation; silent partial success with no recovery contract.
Inspected boundaries: account service state write, billing adapter call, event emission, retry/logging path, and API success contract.
Reuse/placement rationale: transaction ownership stays in the service boundary; billing failure handling is modeled as compensation rather than a generic helper.
Evidence required: transaction boundary or compensation design; partial-failure test and rollback behavior; error/logging/correlation evidence for external API failure.
Output obligations: transaction and partial-success analysis; behavior preservation or intentional behavior-change statement; validation evidence for failure path.
Validation command: not verified; fixture describes expected agent output only.
What evidence proves: failure path and recovery contract are explicit.
What evidence does not prove: production billing provider behavior.
Residual risk: compensation replay owner is still needed from the backend team.
Next gate: quality-test-gate.
