# Repository Persistence Checklist

- Define repository boundary in domain or application language.
- Confirm repository interfaces do not expose ORM-specific objects or query builders.
- Define methods, inputs, outputs, and not-found behavior.
- Map persistence records to domain objects or DTOs intentionally.
- Preserve identity, lifecycle state, nullability, and invariants during mapping.
- Define transaction participation, locking, and consistency expectations.
- Define pagination, ordering, filtering, and soft-delete behavior where relevant.
- Translate storage errors into domain or application outcomes.
- Identify performance risks and required indexes or query plans.
- Add integration tests for mapping, constraints, transactions, and important queries.
