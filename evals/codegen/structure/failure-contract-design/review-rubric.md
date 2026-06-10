# Review Rubric

## Passing Standard

The solution passes when every boundary has typed failure semantics, translation preserves cause safely, retries and fallback are explicit, and negative tests cover the error taxonomy.

## Scoring

- 25 percent taxonomy: retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, and partial failures are distinguishable.
- 25 percent boundary translation: adapter, repository, service, controller, job, and consumer mappings are explicit.
- 20 percent resilience semantics: retry, backoff, fallback, degraded response, compensation, and DLQ behavior are correct.
- 20 percent safety and observability: user messages are safe, logs preserve cause, and metrics/traces correlate.
- 10 percent test evidence: negative tests prove failure semantics.

## Automatic Failure Conditions

- Errors are swallowed with silent fallback.
- Generic errors hide retryability, conflict, validation, permission, timeout, or cancellation semantics.
- Raw DB or SDK errors leak to API responses.
- Partial failure lacks compensation, rollback, DLQ, or explicit acceptance.

## Reviewer Notes

Look for typed error objects or result contracts at boundaries. Penalize catch-all exception blocks that erase cause or turn operational failures into user-safe but unobservable responses.
