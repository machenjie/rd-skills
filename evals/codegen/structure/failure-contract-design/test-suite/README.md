# Test Suite

## Required Checks

- Negative tests distinguish retryable, terminal, validation, permission, conflict, timeout, cancellation, dependency, and partial failure states.
- Silent fallback and generic errors are rejected.
- Raw database and SDK errors are translated before API or user boundaries.
- Async consumer tests cover retry, backoff, DLQ, and poison-message behavior.

## Fixtures

Failure fixtures belong to the payments boundary and must state the source boundary, cause, retryability, user message, and expected observability fields.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Provider timeout remains retryable with backoff.
- Validation and permission failures are terminal.
- Partial capture triggers compensation or explicit accepted degradation.
- Logs preserve diagnostic cause without leaking secrets or PII.
