# Review Rubric

## Passing Standard

The solution passes when data flow and side effects are visible, transaction and event ordering are correct, cache source of truth is named, and tests prevent hidden mapper/getter mutations.

## Scoring

- 25 percent flow map: input through response is traced with each side-effect boundary named.
- 25 percent ordering: transaction, persistence, outbox, publish-after-commit, cache, and external I/O order is correct.
- 20 percent purity boundary: mappers, getters, and policies do not hide external state mutation.
- 20 percent reliability semantics: idempotency, compensation, timeout, cancellation, retry, and cleanup are explicit.
- 10 percent observability: logs and metrics observe without altering behavior.

## Automatic Failure Conditions

- Mapper or getter writes database, mutates cache, publishes event, or calls external API.
- Event is published before commit without explicit safe ordering.
- Cache mutation lacks source of truth and invalidation statement.
- Logging or metrics change control flow or business behavior.

## Reviewer Notes

Look for a clear service/use-case boundary and adapters for infrastructure. Penalize moving hidden side effects from mapper to another generic helper.
