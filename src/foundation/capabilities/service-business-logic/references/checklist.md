# Service Business Logic Checklist

- Select the mode: command use case, query use case, workflow orchestrator, service decomposition, boundary exception, or existing pattern reuse.
- Name the use case, actor, command/query, owning module, included workflow, and excluded responsibilities.
- State source evidence inspected: controllers/handlers/jobs, current services, repositories, domain objects, policies, events, tests, repository graph, project memory, and execution trajectory.
- Record graph/memory/trajectory reuse judgment: accepted, rejected, or not verified with freshness limits.
- Confirm the service is not merely a pass-through wrapper; if it is, document boundary reason, consumers, owner, and review trigger.
- Confirm unrelated workflows are not being grouped into a god service.
- Define inputs, outputs, validation boundary, typed failures, policies, and authorization checks.
- Confirm authorization or scoped lookup precedes protected data access.
- Define transaction boundary, Unit of Work owner, rollback behavior, consistency guarantees, and outside-transaction effects.
- List repositories and domain operations coordinated by the service.
- Keep domain invariants in domain model, value object, policy, or domain service authority.
- Define event emission, outbox/after-commit timing, external effects, timeout, ordering, and consumer consistency assumption.
- Define idempotency, retry, compensation, duplicate handling, and terminal failure behavior.
- Add service-level tests for success, denial, invalid state, not-found/filtered, partial failure, retry/idempotency, and compensation where relevant.
- Map each changed service method, policy order, transaction boundary, domain call, repository call, event/effect, failure path, and test seam to validation evidence or residual risk.
- Name handoff boundaries for domain logic, repository persistence, controller/API, transaction consistency, idempotency/retry, async job, security, reliability, and quality gates.
- State evidence limits before handoff.
