# Review Rubric

## Passing Standard

The solution passes when dependency creation has one visible composition root, reusable clients are scoped correctly, tests can override seams without changing production semantics, and long-lived resources are cleaned up.

## Scoring

- 30 percent lifecycle correctness: every dependency has owner, scope, construction, and shutdown policy.
- 25 percent client and pool reuse: no per-operation reusable HTTP, DB, Redis, Kafka, or SDK client construction.
- 20 percent graph discipline: service locator and circular dependencies are removed or justified.
- 15 percent configuration binding: typed, validated configuration drives wiring safely.
- 10 percent testability: overrides are explicit and do not mutate production global state.

## Automatic Failure Conditions

- HTTP, DB, Redis, Kafka, SDK clients, or pools are constructed per request or per message.
- A service locator hides dependency ownership.
- Circular dependency graph remains unexplained.
- Shutdown cleanup for pool, timer, subscription, file, socket, or client is missing.

## Reviewer Notes

Prefer boring constructor, factory, or provider injection at the composition root. Penalize clever lazy globals unless ownership, startup validation, and cleanup are explicit.
