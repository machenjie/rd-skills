# Async Job Design Checklist

- Define job name, trigger, owner, and expected outcome.
- Use stable identifiers in payload and document any intentional snapshot semantics.
- Define idempotency key and duplicate-delivery behavior.
- Define execution steps, ordering, and transaction boundaries.
- Set timeout, attempt budget, and terminal states; select any retry schedule from the actual failure class, service guidance, and existing retry owner.
- Classify transient, permanent, cancelled, and unknown-outcome failures.
- Define status visibility for users, operators, or dependent systems.
- Define cancellation behavior and compensation for committed side effects.
- Use the signals needed to observe job progress and failures. Name the selected terminal disposition and recovery owner; add logs, metrics, traces, correlation, or failure queues only where existing state and evidence leave a material gap.
- Run current proof for the affected success, duplicate delivery, retry, timeout, cancellation, and partial-failure paths; add tests only for a material gap.
