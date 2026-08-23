# State Distinction and Outcome Patterns

Use this benchmark-pattern Reference only for the named state-distinction-and-outcome-patterns decision.

## Outcome Comparisons

- Available or idle: define available actions, empty meaning, focus entry, and refresh behavior.
- Pending or unknown: distinguish accepted, running, disconnected, timed out, or unreconciled work; decide progress, repeat safety, cancellation truth, stale data, and urgency.
- Durable success or empty: require authoritative outcome and cardinality before choosing acknowledgement, guidance, follow-up, or silence.
- Rejected, denied, missing, or filtered: apply typed outcome and disclosure policy before explanation and recovery.
- Failed or retryable: bind retry, backoff, preserved input, diagnostics, and support to mechanism, idempotency, provider guidance, and cost.
- Partial, optimistic, or rolled back: preserve reconciliation, compensation, duplicate prevention, conflicts, and announcements when local and durable state differ.
- Treat HTTP and network results as exchanges, not complete operation state.

Reject a spinner that hides loading, timeout, and error, or success copy on `202 Accepted` before durable completion.
