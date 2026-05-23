# Review Rubric

## Passing Standard

The implementation must make payment creation idempotent across retries and
concurrent requests while preserving a clear audit trail and safe client
responses. It must demonstrate durable state, explicit transaction boundaries,
and tests that would fail against the starter behavior.

## Scoring

- 30 percent correctness for idempotency behavior, conflict handling, and state transitions.
- 20 percent data integrity for transactions, unique constraints, and money precision.
- 20 percent test quality for concurrency, timeout, decline, and regression coverage.
- 15 percent security and privacy for redaction, authorization boundaries, and safe errors.
- 15 percent maintainability for simple boundaries, readable code, and documentation.

## Automatic Failure Conditions

- Duplicate provider charges are possible for the same key and payload.
- Idempotency is stored only in memory.
- Money values are represented with binary floating point.
- Sensitive payment source or secret values appear in logs or errors.

## Reviewer Notes

Prefer solutions that reserve the idempotency key before external side effects
and make recovery from provider uncertainty explicit. Award partial credit for
well documented limitations only when tests still protect the critical paths.