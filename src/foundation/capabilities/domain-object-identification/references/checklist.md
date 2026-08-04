# Domain Object Identification Checklist

- List candidate entities, immutable value objects, aggregate roots, child entities, resources, policies, boundary models, and read models.
- Record the selected classification and rejected alternatives.
- Define entity identity and value equality, including no independent identity, normalization, immutability, and replacement semantics.
- Define the aggregate root as the aggregate update and invariant entry point.
- Define object owner, tenant scope, writer authority, accepted writers, rejected writers, and mutation entry points.
- Define lifecycle and important state transitions.
- Define invariants owned by each object or aggregate.
- Define relationships, cardinality, and optionality.
- Identify aggregate boundaries and consistency requirements.
- Identify external resources and API representations.
- Identify persistence, permission, and event implications.
- Record DTO, schema, table, event, provider, UI, and read-model mappings.
- Reject objects created only from UI labels, table names, DTOs, comments, or proximity.
- Record current evidence, proof limits, and residual risks.
