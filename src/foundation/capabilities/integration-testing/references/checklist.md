# Integration Testing Checklist

- Identify the real boundary under test.
- Include realistic schema, auth context, serialization, and configuration where relevant.
- Control external dependencies through sandbox, local service, fake, or contract-checked stub.
- Assert persisted state, emitted events, responses, and side effects.
- Cover failure, timeout, rollback, retry, or partial-write paths when possible.
- Isolate test data and clean up durable side effects.
