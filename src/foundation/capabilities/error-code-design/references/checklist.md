# Error Code Design Checklist

- Define stable error code and category.
- Map each error to status code or transport status.
- Define user-safe message and client-visible action.
- Define developer action and support diagnostic path.
- Mark retryable, non-retryable, conflict, validation, and authorization cases.
- Include idempotency guidance for retryable side effects.
- Include correlation ID or trace reference behavior.
- Redact internal exception, provider, and database detail.
- Define tests for error mapping and client behavior.
