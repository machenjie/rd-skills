# Interaction State Modeling Checklist

- Define loading, queued, and refreshing states.
- Define empty state separately from filtered empty, not found, no access, and load failure.
- Define validation, system error, dependency error, and timeout states.
- Define success state and whether it means accepted, complete, or durable.
- Define disabled states and user-accessible explanation.
- Define partial completion and partial data states.
- Define permission-denied state without leaking restricted details.
- Define allowed actions, blocked actions, retry, cancellation, and navigation.
- Define preserved input and recovery behavior.
- Map states to backend signals and tests.
