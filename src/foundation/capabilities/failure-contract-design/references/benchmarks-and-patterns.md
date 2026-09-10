# Failure Contract Design Benchmarks And Patterns

- Define a machine-distinguishable failure contract at each changed material boundary; message text alone is not stable.

Select among validation, permission, not-found, conflict, timeout, cancellation, dependency, retryable, terminal, degraded, partial, poison-message, and internal states. For each, fix caller action, operator action, retry stance, translation boundary, and escalation.

- Validation or permission failures require changed input or authority, not unchanged retry.
- Conflict retry requires a precondition contract.
- Timeout preserves unknown outcome; cancellation preserves caller intent and separates cleanup failure or continued work.
- Dependency failures translate to local typed meaning with authorized cause.
- Degraded results name unavailable or stale data and policy owner.
- Partial results name completed/incomplete effects and recovery owner; require duplicate-safety proof before retrying escaped effects.

Translate raw dependency/framework failure to a local type, then safe public response/event/job/UI meaning, while authorized diagnostics retain cause, boundary, correlation, and redaction. Exclude secrets, protected existence, provider payloads, SQL, paths, prompts, and tool output.

Reject null/empty success, raw provider exceptions, collapsed INTERNAL_ERROR, unknown-as-retryable, generic partial errors, and message-only assertions. Return the taxonomy/translation comparison, selected meanings, partial/degraded ownership, and specialist handoffs.
