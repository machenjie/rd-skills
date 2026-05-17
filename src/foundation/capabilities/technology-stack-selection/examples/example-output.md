# Example Output

```markdown
## Stack Decision

Decision: Keep the existing web framework and add a small queue-backed worker.
Why: The requirement is asynchronous processing, not a new service platform.
Rejected: New microservice framework, because it adds deploy and observability cost without isolation needs.
Reversibility: Reversible with feature flag and queue drain plan.
Owners: Platform team owns queue operations and upgrade cadence.
Quality Gate: Accept after load test and rollback dry run.
```
