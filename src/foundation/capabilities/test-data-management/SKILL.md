---
name: test-data-management
description: "`analysis-agent`/`task-agent`/`review-agent`: use when fixtures, factories, seeds, isolation, cleanup, or sensitive test-data rules change; skip when test data is unaffected."
---

# test-data-management

## Registry Trigger

**Use when**

- manage fixtures factories seeded data isolation cleanup and sensitive data rules

**Do not use when**

- no task-local test data management decision is required

## Skill Role

Define fixture meaning, deterministic generation, namespace and isolation, relationship integrity, sensitive-data controls, cleanup, and evidence freshness. Exclude test portfolios, database design, and environment provisioning.

## High-Value Rules

- **Design data from the failure mechanism and oracle.** Include the smallest records, relationships, state, boundary values, and forbidden conditions needed to exercise the named behavior rather than a generic fixture universe.
- **Give created state an owner and namespace.** Select transaction, disposable resource, unique tenant or key space, seeded snapshot, or targeted cleanup from actual commit and asynchronous-effect semantics.
- **Keep generation deterministic where evidence depends on it.** Control clocks, randomness, identifiers, ordering, locale, and external responses while preserving the boundary behavior the test intends to prove.
- **Preserve domain and storage relationships.** Build valid defaults through owned factories or builders, then vary only the attributes needed for the case so accidental invalidity does not obscure the target mechanism.
- **Use synthetic or approved protected data.** Apply current classification, minimization, access, masking, retention, and deletion policy; do not copy production secrets or personal records into uncontrolled fixtures.
- **Clean independently committed and asynchronous effects.** Track created identifiers, drain or reconcile queued work, and bound destructive cleanup so failed or parallel runs cannot delete another owner's state.
- **Tie evidence to data version and environment.** Record schema, fixture source, seed or generator version, dependency versions, and material data assumptions, then refresh after changes that can alter the oracle.

## Anti-Patterns

- Share mutable fixture state across cases or depend on execution order, machine time, or uncontrolled identifiers.
- Use a large production-like snapshot that hides which records and relationships cause the behavior.
- Rely on rollback cleanup when effects commit separately, run asynchronously, or leave external resources behind.

## Stop Conditions

Escalate when test ownership or namespace is absent, cleanup can reach shared data, or representative relationships cannot be constructed. Also escalate when sensitive data lacks approved handling, asynchronous effects cannot reconcile, or fixture drift makes results ambiguous.

## Output Contract

- test-data decision with failure-focused fixtures, deterministic generation, isolation and ownership, relationship integrity, sensitive-data controls, cleanup behavior, freshness evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | fixture ownership isolation privacy or cleanup mechanisms remain undecided | one deterministic owned fixture strategy covers the changed boundary | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | tests change fixtures randomness time sensitive data or external cleanup | test data remains deterministic isolated private and cleanup-safe | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | fixture ownership isolation or privacy claims need fresh proof | current factories cleanup paths and parallel tests prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
