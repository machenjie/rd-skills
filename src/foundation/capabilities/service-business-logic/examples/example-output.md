# Example Output

```markdown
## Application Orchestration Contract

Use case: cancel a subscription for an authorized account actor.

Ownership:
- The application service owns authorization order, transaction scope, domain invocation, persistence coordination, and reversal handoff.
- The subscription aggregate owns allowed and denied cancellation transitions.
- The repository owns visibility and storage failures; the provider worker owns reversal retries.

Sequence:
- Establish account scope through a non-disclosing lookup.
- Invoke the domain cancellation operation.
- Commit subscription state and a durable reversal request together.
- Dispatch provider work after commit.

Failures:
- Preserve denied, inaccessible, invalid transition, duplicate request, unknown provider outcome, and terminal reversal states.
- Reconcile a provider success whose local result record is missing before replay.

Evidence limit:
- Current service and transaction fixtures cover the inspected sequence; provider partitions and live retry operations remain outside this claim.
```
