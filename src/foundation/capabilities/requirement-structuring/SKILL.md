---
name: requirement-structuring
description: "`analysis-agent`: use when raw requests need behavior, actors, scope, non-goals, constraints, deliverables, acceptance, or test traceability; skip when structure already exists."
---

# requirement-structuring

## Registry Trigger

**Use when**

- structure raw request into scope constraints dependencies and deliverables

**Do not use when**

- no task-local requirement structuring decision is required

## Skill Role

Transform raw requests into sourced current behavior, desired outcomes, actors, scope, exclusions, constraints, dependencies, risks, deliverables, acceptance oracles, and unresolved decisions. Exclude architecture and implementation planning.

## High-Value Rules

- **State current behavior observably.** Describe inputs, actors, system responses, state and side effects, errors, and evidence source rather than implementation calls or unsupported inference.
- **Express desired outcome before solution.** Name the changed behavior and consequence for affected actors, then separate required outcome from proposed mechanism, technology, or file placement.
- **Bound scope by behavior and ownership.** Identify included surfaces, consumers, data, environments, and owners plus explicit exclusions whose absence can be checked.
- **Source constraints and assumptions.** Distinguish contractual, policy, compatibility, security, capacity, delivery, and user constraints from provisional assumptions, each with authority and reopen condition.
- **Expose dependencies and unresolved decisions.** Record upstream inputs, downstream consumers, external owners, sequencing dependencies, contradictory evidence, and questions that materially change implementation or proof.
- **Make deliverables change-specific.** Include only artifacts, code, migration, documentation, operation, or evidence outputs needed to realize and verify the bounded outcome.
- **Trace acceptance to observable risk.** Connect normal, boundary, negative, recovery, and non-goal checks to changed behavior and consequence without prescribing a fixed test portfolio.

## Anti-Patterns

- Rewrite a requested solution as a requirement without verifying the underlying outcome and constraint.
- Use vague scope labels or exclusions that cannot be observed in code, contract, data, UI, operation, or evidence.
- Fill missing authority, defaults, thresholds, dependencies, or acceptance behavior with plausible assumptions and present them as settled facts.

## Stop Conditions

Escalate when current behavior cannot be observed, actor or outcome is ambiguous, material constraints conflict, or scope crosses unowned consumers or data. Also escalate when an unresolved decision changes architecture or risk, or consequential behavior lacks an acceptance owner.

## Output Contract

- structured requirement with sourced current behavior, desired outcomes, actors, scope and exclusions, constraints and assumptions, dependencies, risks, deliverables, acceptance trace, unresolved decisions, and owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | current desired scope constraint or dependency framing remains ambiguous | accepted behavior-first structured requirement already fixes every requirement boundary | analysis-agent | option-comparison, decision-record |
| [checklist](references/checklist.md) | decision-checklist | structured requirement lacks observable behavior actors non-goals constraints or acceptance | accepted structured requirement contains every required task-local field | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | current-behavior constraint dependency or non-goal claims need proof | fresh source and owner evidence substantiate every structured requirement fact | analysis-agent | evidence-record, proof-limit, residual-risk |
