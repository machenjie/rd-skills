# Domain Object Identification Evidence Patterns

Use this reference when object-identification closure depends on validation freshness, prior source or task evidence claims, writer scans, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second object taxonomy.

## Object-Claim-To-Validation Map

| Object claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Entity identity is stable | Current source path, identity source, tenant/merge/split semantics, writer or test evidence | The inspected entity can be distinguished over time in the named boundary | External ids, imports, or future merge paths outside scope are safe |
| Value equality is attribute-based | No-independent-identity decision, constructor/factory rule, normalization, immutability, replacement semantics, equality tests or owner review, and serialization boundary | Tested values compare by declared attributes and change by replacement | All locale, precision, timezone, or provider formats are covered |
| Aggregate boundary is enforceable | Invariant list, aggregate-root update entry point, writer scan, relationship cardinality, and transaction/consistency note | Inspected invariants have one enforceable owner and entry point | Production races are eliminated without transaction or concurrency evidence |
| Resource is a boundary model | Internal/external object map, generated/API/event path, compatibility owner, and mapping test or review | External naming is intentionally translated | Unknown consumers or uninspected generated clients are compatible |
| Read model stays read-only | Projection source, refresh owner, blocked mutation path, and test or review artifact | Inspected projection is not write authority | Ad hoc support scripts or external tools cannot mutate state |
| Mutation authority is not split | Writer inventory, accepted owner, rejected or rerouted writers, and denied mutation cases | Inspected writers have a single authority path | Future jobs, scripts, or runtime-only admin tools remain covered |
| Same-term reuse is controlled | Context map, source paths using the term, owning language, translation point, and rejected meanings | The inspected term has a bounded meaning in the named context | All docs, reports, or downstream teams use the same meaning |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old incidents, prior naming decisions, generated schemas, and docs as selectors until current source and fresh validation confirm them.
- Accept prior "this table is the object", "resource equals aggregate", "term owner is known", or "writer path is unique" claims only when current source, schemas, tests, events, and owners still match.
- Mark evidence stale after edits to object names, identity fields, lifecycle states, writer paths, schemas, generated clients, events, docs, reports, or validation outputs.
- For each final object-identification claim, cite current command, test, report, or owner-review evidence. Coverage includes the selected classification, rejected alternatives, identity or value equality and immutability, lifecycle, aggregate/invariants, writer authority, relationship, mappings, and downstream handoff; unsupported claims retain `not_run` and residual risk.

- If data migration, object merge/split, production writer disablement, or event replay, record environment, owner approval, stop condition, rollback plan, and redaction rule.
- If production telemetry, audit, or consumer query, keep access read-only or approved-connector-scoped, aggregate sensitive labels, and redact tenant/user/secret-bearing fields.

## Proof Limits And Residual Risks

- Source and test evidence proves only the inspected writers, mappings, lifecycle transitions, and equality cases.
- Language equality/hash/reference documentation does not prove domain identity or value semantics.
- Unknown external writers, reflective/generated mutation, cross-service replay, and production races remain residual risks until their owners supply current evidence.
