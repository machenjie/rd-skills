---
name: domain-object-identification
description: Identifies entities, value objects, aggregates, resources, ownership, lifecycle, invariants, and relationships for product-domain changes.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "12"
changeforge_version: 0.1.0
---

# Mission

Establish the domain object inventory needed to place behavior, persistence, permissions, events, and tests on the correct conceptual model.

# When To Use

Use this capability when a change introduces or modifies entities, value objects, aggregates, resources, ownership, lifecycle states, relationships, identifiers, or invariants.

# Do Not Use When

Do not use this capability to mirror database tables without domain reasoning, rename implementation classes for style, or create speculative domain objects beyond the approved scope.

# Non-Negotiable Rules

- Distinguish entities, value objects, aggregates, resources, policies, and read models.
- Identify ownership, lifecycle, invariants, and relationship cardinality.
- Define source of identity and equality semantics.
- Identify which object owns each rule and transition.
- Do not let UI labels or storage tables define the domain model by default.

# Industry Benchmarks

Use domain-driven design tactical modeling, aggregate consistency review, resource modeling, lifecycle analysis, data ownership review, and API contract design practices as benchmarks.

# Selection Rules

Select this capability when the main question is what domain concepts exist and who owns their behavior. Prefer business-rule-extraction when objects are known but rules are scattered. Prefer data-model-design when persistence structure is the main deliverable.

# Risk Escalation Rules

Escalate when object boundaries affect consistency, tenant ownership, money movement, regulated records, audit history, migration design, external API resources, or event semantics.

# Critical Details

Entities require stable identity across time. Value objects require equality by attributes and should not hide lifecycle state. Aggregates own invariants that must be transactionally protected. Resources are externally exposed representations and may not equal internal aggregates. Ownership includes business owner, data owner, tenant scope, and mutation authority.

# Failure Modes

- Database tables are accepted as domain objects without behavior analysis.
- Value objects gain hidden identity and lifecycle.
- Aggregate boundaries are too large, creating lock contention and broad transactions.
- Aggregate boundaries are too small, allowing invariants to be violated.
- External resource names overwrite internal domain language without review.

# Output Contract

Return a domain object inventory with: object name, category, identity, owner, lifecycle, invariants, relationships, aggregate boundary, resource exposure, persistence implications, permission implications, event implications, and tests.

# Quality Gate

The inventory is complete only when rules, state transitions, permissions, persistence, and events can be assigned to explicit domain owners.

# Used By

- domain-impact-modeler
- data-api-contract-changer
- backend-change-builder

# Handoff

Hand off to business-rule-extraction for invariants, state-machine-modeling for lifecycle, permission-boundary-modeling for authorization, or data-model-design for persistence.

# Completion Criteria

The capability is complete when domain concepts are named with ownership, lifecycle, invariants, and relationships clear enough to guide implementation.
