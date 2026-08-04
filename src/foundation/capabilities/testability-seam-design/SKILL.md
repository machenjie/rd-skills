---
name: testability-seam-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when behavior needs deterministic seams for time, randomness, UUIDs, collaborators, or external I/O; skip when seams are adequate."
---

# testability-seam-design

## Registry Trigger

**Use when**

- testability seam planning
- testability seam
- testability seam public behavior boundary dependency injection fake stub mock spy characterization private helper not exported deterministic clock randomness UUID external IO reset observation contract

**Do not use when**

- no task-local testability seam design decision is required
- fixture builder seed snapshot golden namespace sensitive-data or asynchronous data cleanup ownership is the unresolved decision

## Skill Role

Define the smallest production-safe control, reset, and observation seam for nondeterminism, collaborators, and external effects. Consume test-data lifecycle decisions from `test-data-management`; exclude test portfolios and architecture redesign.

## High-Value Rules

- **Start from the behavior and failure mechanism.** Name the observable outcome, uncontrolled input, and evidence the seam should enable before choosing injection, wrapper, fake, hook, or interface shape.
- **Place the seam at a stable ownership boundary.** Prefer an existing composition, adapter, clock, repository, client, scheduler, or policy boundary over exporting private helpers or widening production APIs only for tests.
- **Control nondeterminism at its source.** Inject or capture time, randomness, identifiers, environment, scheduling, and external responses where they enter the behavior, preserving production defaults and concurrency semantics.
- **Match substitutes to material semantics.** Model state, ordering, error, timeout, cancellation, retry, transaction, and authorization behavior needed by the risk; route real-boundary proof to integration or contract testing.
- **Keep test control separate from business authority.** A seam may supply inputs or observations but should not bypass validation, permission, invariants, lifecycle, or side-effect ownership present in production.
- **Expose a seam reset contract.** Define only the control and observation needed to honor accepted `test-data-management` fixture, namespace, sensitive-data, asynchronous-cleanup, and lifecycle decisions.
- **Prove the seam improves evidence without distorting design.** Show the named failure becomes reproducible and the production path remains unchanged in public behavior, wiring, and resource ownership.

## Anti-Patterns

- Export a private method, add production flags, or expose mutable state solely to assert implementation details.
- Introduce a broad interface or dependency-injection layer when a smaller existing boundary controls the risk.
- Use a fake that returns desired values while omitting the state transition, failure, ordering, or ownership semantics under test.

## Stop Conditions

Escalate unowned seams, weakened trust or invariant boundaries, test/production wiring drift, unfaithful substitutes, unsafe seam reset, or claims requiring a real dependency. Route unresolved test-data lifecycle ownership to `test-data-management`.

## Output Contract

- testability-seam decision with behavior and failure mechanism, stable placement, controlled inputs, substitute fidelity, production-default preservation, accepted test-data decision, seam reset/observation obligations, evidence gain, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | real boundary fake stub mock or deterministic seam remains undecided | one existing production seam exposes the failure mechanism | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | test design affects visibility doubles nondeterminism seam reset or characterization after test-data ownership is accepted | test-data ownership is unresolved or public behavior is testable without a new seam | analysis-agent, task-agent, review-agent | checklist-result, validation-plan |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | double fidelity determinism or seam reset compliance with an accepted test-data decision needs proof | test-data ownership is unresolved or current tests prove each seam claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
