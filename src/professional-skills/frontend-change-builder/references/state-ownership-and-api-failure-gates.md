# State Ownership and API Failure Gates

Use this Reference only for the named state-ownership-and-api-failure-gates decision.

## Decision Rules

- Assign local, form, URL, server-cache, context, global-store, or derived state to its current owner; record invalidation, reset, persistence, and failure transitions.
- Map loading, empty, validation, permission, conflict, timeout, retryable, terminal, and dependency failures to truthful messages, preserved input, retry stance, and diagnostic owner.
- Keep DTO or view-model mapping, null and default semantics, generated clients, and error contracts explicit.
- Reject global promotion without current cross-feature consumers and reject a generic catch that collapses failure meanings or hides recovery.

Return the state decision, failure contract, recovery behavior, and residual risk.
