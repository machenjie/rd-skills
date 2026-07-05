# Transaction Consistency Checklist

- Name the invariant each transaction must protect.
- Define the minimal data and operations that must commit atomically.
- State isolation level, locks, conflict detection, and timeout budget.
- Keep slow remote calls outside database transactions where possible.
- Define optimistic or pessimistic concurrency behavior and retry limits.
- Avoid distributed transactions unless explicitly justified.
- Define local transaction plus event, outbox, compensation, or reconciliation where appropriate.
- Test lost updates, duplicate retries, timeouts, and partial failure.
