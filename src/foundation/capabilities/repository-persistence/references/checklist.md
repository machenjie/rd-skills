# Repository Persistence Checklist

- Define repository boundary in domain or application language.
- Confirm whether ORM, session, or query objects cross the public boundary and record any accepted lifecycle or query effects.
- Define methods, inputs, outputs, and not-found behavior.
- Map persistence records to domain objects or DTOs intentionally.
- Preserve identity, lifecycle state, nullability, and invariants during mapping.
- Define transaction participation, locking, and consistency expectations.
- Define pagination, ordering, filtering, and soft-delete behavior where relevant.
- Translate storage errors into domain or application outcomes.
- Identify performance risks and required indexes or query plans.
- Obtain real or equivalent-store evidence for changed mapping, constraints, transactions, filters, and important queries, or record the proof gap.
