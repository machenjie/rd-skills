# Test Data Management Checklist

- Use deterministic synthetic fixtures or factories.
- Isolate data by transaction, namespace, tenant, sandbox, or reset strategy.
- Exclude live or usable secret/session material and sensitive user data; label synthetic inert token or cookie fixtures as non-secret.
- Control time, randomness, generated identifiers, locale, and timezone.
- Define cleanup for databases, caches, files, queues, and external sandboxes.
- Keep fixtures readable and scoped to the behavior under test.
