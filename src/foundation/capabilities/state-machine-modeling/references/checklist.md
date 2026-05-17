# State Machine Modeling Checklist

- Identify object or workflow whose lifecycle is being modeled.
- List all states and terminal states.
- Define allowed transitions with trigger, actor, and guard.
- Define illegal transitions and expected rejection behavior.
- Define side effects that occur after successful transition.
- Define emitted events and audit records.
- Define failure, timeout, retry, cancellation, and recovery transitions.
- Define concurrency and duplicate-transition handling.
- Confirm authoritative enforcement layer.
- Map transitions to unit, integration, or E2E tests.
