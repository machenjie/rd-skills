# Test Data Management Checklist

- Use deterministic synthetic fixtures or factories.
- Isolate data by transaction, namespace, tenant, sandbox, or reset strategy.
- Avoid secrets, credentials, tokens, and sensitive user data.
- Control time, randomness, generated identifiers, locale, and timezone.
- Define cleanup for databases, caches, files, queues, and external sandboxes.
- Keep fixtures readable and scoped to the behavior under test.
