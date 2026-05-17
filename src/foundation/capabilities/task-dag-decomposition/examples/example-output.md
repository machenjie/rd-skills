# Example Output

```markdown
## Task DAG

T1: Add idempotency persistence
- Depends on: none.
- Scope: repository and migration files.
- Verify: migration test and duplicate key behavior.
- Rollback: additive table can remain unused.

T2: Use idempotency in webhook handler
- Depends on: T1.
- Scope: webhook handler only.
- Verify: duplicate event unit tests.
- Rollback: disable handler path with existing feature flag.

T3: Add provider retry integration test
- Depends on: T2.
- Scope: integration tests.
- Verify: retry returns success without duplicate invoice mutation.

Parallel group:
- Documentation update can run after T2 while T3 is prepared.
```
