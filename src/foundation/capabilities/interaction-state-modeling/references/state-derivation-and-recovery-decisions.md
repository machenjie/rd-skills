# State Derivation and Recovery Decisions

Use this Reference only for the named state-derivation-and-recovery-decisions decision.

## Decision Rules

1. Identify the authoritative outcome and whether a transport response proves durable completion.
2. Determine whether repeat, cancel, or navigation can duplicate or abandon effects.
3. Offer retry only when idempotency, provider guidance, operation cost, and authority make it safe.
4. Derive action availability from duplicate risk, prerequisites, cancellation, and supported concurrency.
5. Apply disclosure policy before distinguishing denied, missing, filtered, or failed states.
6. Keep unknown, partial, and optimistic outcomes distinct until reconciliation closes them.

Model optimistic rejection, conflicting updates, rollback, duplicate prevention, accepted or queued work, partial application, completion, failure, compensation, refresh, and stale views only where the backend contract exposes them. Reject an optimistic delete without rollback or timeout copy that falsely says cancelled.
