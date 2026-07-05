# Security Checks

## Threat Surface

Order events may contain customer data and can trigger notification or indexing
side effects outside the main transaction.

## Required Checks

- Reject subscriber logs that expose sensitive order data.
- Reject observer side effects that run before commit.
- Verify subscriber failures do not cause duplicate or unauthorized side effects.

## Rejection Cases

- Reject an observer that publishes before the order invariant is committed.
- Reject unbounded fan-out that can leak data through uncontrolled subscribers.
- Reject missing subscriber error isolation.
