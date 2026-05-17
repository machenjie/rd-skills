---
name: domain-logic-implementation
description: Implements domain invariants near the domain model or domain service and prevents duplicated inconsistent rules across layers.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "39"
changeforge_version: 0.1.0
---

# Mission

Implement domain logic so invariants, lifecycle rules, calculations, and policies are enforced near the domain model or domain service that owns them.

# When To Use

Use this capability when a change adds or modifies domain objects, aggregate behavior, invariants, calculations, state transitions, domain services, policies, or rule placement.

# Do Not Use When

Do not use this capability to scatter domain rules across controllers, UI code, database scripts, tests, or unrelated services.

# Non-Negotiable Rules

- Domain invariants must be enforced near the domain model, aggregate, value object, or domain service that owns the rule.
- Rules must have one authority and must not be duplicated inconsistently across layers.
- Invalid state transitions must be rejected before persistence.
- Domain logic must not depend on transport, framework, or persistence-specific objects.
- Domain operations must expose clear success and failure outcomes.
- Tests must cover allowed behavior, denied behavior, boundary values, and state transitions.

# Industry Benchmarks

Use domain-driven design tactical patterns, aggregate invariants, value object validation, domain service placement, state machine discipline, ubiquitous language, and property or boundary testing as benchmarks.

# Selection Rules

Select this capability when rule authority or invariant enforcement is primary. Prefer service-business-logic when orchestration and transactions dominate. Prefer business-rule-extraction when rules are still being discovered.

# Risk Escalation Rules

Escalate when rules affect money, permissions, compliance, lifecycle terminal states, cross-aggregate consistency, irreversible transitions, or calculations used by external contracts.

# Critical Details

Domain logic should make invalid states difficult or impossible to persist. Controllers and services may perform preliminary checks, but the domain authority must still enforce core invariants. Some rules belong in domain services when they require multiple domain objects or policies. Persistence constraints can reinforce domain rules, but they are not a substitute for readable domain behavior.

# Failure Modes

- The same rule exists in frontend, controller, service, and database with different edge cases.
- Domain objects are passive data bags while services mutate fields directly.
- Invalid lifecycle transitions persist because only UI controls were hidden.
- Domain code accepts ORM objects and becomes tied to storage behavior.
- Tests prove happy paths but miss denied transitions and boundary values.

# Output Contract

Return a domain implementation contract with: domain owner, invariants, operations, allowed transitions, rejected transitions, value objects, policy or domain service needs, failure outcomes, persistence constraints that reinforce rules, and tests.

# Quality Gate

The domain implementation is complete only when each invariant has one authority, invalid states are rejected near the domain, and tests prove both allowed and forbidden behavior.

# Used By

- backend-change-builder
- domain-impact-modeler

# Handoff

Hand off to business-rule-extraction for unclear rules, state-machine-modeling for complex lifecycle transitions, service-business-logic for orchestration, or repository-persistence for persistence mapping.

# Completion Criteria

The capability is complete when domain rules are centralized, enforceable, persistence-independent, and covered by focused tests.
