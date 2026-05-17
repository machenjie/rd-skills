# Service Business Logic Checklist

- Name the use case or workflow the service owns.
- Confirm the service is not merely a pass-through wrapper.
- Confirm unrelated workflows are not being grouped into a god service.
- Define inputs, outputs, policies, and authorization checks.
- Define transaction boundary and consistency guarantees.
- List repositories and domain operations coordinated by the service.
- Keep domain invariants in domain model or domain service authority.
- Define event emission, external effects, and ordering.
- Define idempotency, retry, and compensation needs.
- Add service-level tests for success, denial, invalid state, and partial failure.
