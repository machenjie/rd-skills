# Integration Testing Checklist

- Identify the real boundary under test.
- Include realistic schema, auth context, serialization, and configuration where relevant.
- Control external dependencies through sandbox, local service, fake, or contract-checked stub.
- Assert persisted state, emitted events, responses, and side effects.
- Inject each task-relevant failure mechanism and assert the expected response, durable state, retry or terminal outcome, and forbidden partial effects.
- For concurrent or eventually consistent seams, assert allowed terminal outcomes and forbidden durable effects with an observable bounded wait.
- Consume the `test-data-management` fixture, namespace, sensitive-data, and cleanup decision; verify that the exercised seam honors it.
- Own and verify cleanup only for disposable non-data seam infrastructure.
