# Domain Logic Implementation Checklist

- Identify the domain model, aggregate, value object, or domain service that owns each rule.
- List invariants, calculations, policies, and lifecycle transitions.
- Confirm rules are not duplicated inconsistently across UI, controller, service, and persistence layers.
- Reject invalid state before persistence.
- Keep transport, framework, and persistence-specific objects out of domain logic.
- Define explicit success and failure outcomes for domain operations.
- Reinforce critical invariants with persistence constraints where appropriate.
- Cover boundary values, invalid transitions, and exceptional cases in tests.
- Identify cross-aggregate or eventual-consistency limits.
- Escalate unclear rule authority before implementation.
