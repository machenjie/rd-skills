---
name: unit-testing
description: "`analysis-agent`/`task-agent`/`review-agent`: use when logic, rules, invariants, branches, edges, or failure paths need isolated tests; skip without a unit-test decision."
---

# unit-testing

## Registry Trigger

**Use when**

- test pure logic edge cases invariants branches and failure paths

**Do not use when**

- no task-local unit testing decision is required

## Skill Role

Prove local observable behavior through deterministic seams, faithful doubles, strong assertions, cleanup, and explicit unit-proof limits. Exclude real-boundary, journey, portfolio, and release decisions.

## High-Value Rules

- **Separate ordinary behavior proof from regression proof.** Recreate changed inputs, states, branches, or dependency responses and assert observable allowed and denied outcomes without inventing a prior failure.
- **Consume known-failure evidence conditionally.** When an accepted defect, incident, or review finding exists, use `regression-testing` for causal trigger, counterfactual, fixture, and same-pattern decisions.
- **Assert stable observable behavior.** Prefer public outcomes and important invariants over private call order or helper structure, and cover denied or absent effects where silent mutation would matter.
- **Control relevant nondeterminism.** Place owned seams around clock, randomness, identifiers, scheduling, environment, and mutable global state only where they affect the rule under test.
- **Match doubles to the risky contract.** Preserve required dependency semantics without inferring infrastructure behavior from a convenient fake.
- **Challenge consequential assertions proportionately.** Invert a guard or perturb a fixture when it materially improves confidence; require red-before-fix, mutation, or fault evidence only under the selected regression contract.
- **Own isolation and cleanup.** Reset changed state and release fixtures, scheduled work, or temporary resources across success, failure, and cancellation paths.
- **State the proof boundary.** Unit evidence covers inspected local behavior, not framework wiring, persistence constraints, serialization, network compatibility, provider behavior, production timing, or release readiness.

## Anti-Patterns

- Call an ordinary behavior test a regression guard without an accepted prior failure, or claim known-failure coverage without reproducing its mechanism.
- Couple tests to private structure so a behavior-preserving refactor invalidates the evidence.
- Retry or quarantine leaked-state failures, or promote a green unit command to system proof.

## Stop Conditions

Escalate when behavior or invariants are unclear, the causal failure cannot be represented locally, a required seam lacks an owner, or the double cannot preserve material boundary semantics. Also escalate when cleanup can contaminate other evidence or the claim depends on a real integration outside unit scope.

## Output Contract

- unit behavior proof with changed local behavior or invariant, observable and denied outcomes, deterministic seams, double-fidelity limits, proportionate assertion challenge, cleanup evidence, and explicit proof boundary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Behavior seam double assertion-challenge cleanup or selected regression patterns remain undecided | Root rules determine one narrow behavior proof and owned cleanup path | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Several failure negative-proof nondeterminism cleanup or proof-limit decisions must close together | One changed local rule has a locked mechanism denied outcome cleanup and explicit proof limit | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Behavior or selected regression denied-outcome seam double fidelity assertion cleanup or unit-scope claims need fresh proof | Fresh behavior seam assertion cleanup command and proof-limit evidence close the applicable claims | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
