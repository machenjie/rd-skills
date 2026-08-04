---
name: use-case-modeling
description: "`analysis-agent`: use when actors, goals, preconditions, triggers, paths, guarantees, postconditions, or acceptance traces need modeling; skip when no use-case decision exists."
---

# use-case-modeling

## Registry Trigger

**Use when**

- model use cases actors preconditions postconditions and success guarantees

**Do not use when**

- no task-local use case modeling decision is required

## Skill Role

Define actor goal, authority, trigger, preconditions, success and alternative paths, guarantees, failure consequences, and traceability for a system interaction. Exclude persona research and detailed UI flow.

## High-Value Rules

- **Bound one goal and system responsibility.** Name the initiating actor, affected parties, desired outcome, system boundary, included variants, and excluded goals so the use case does not become a feature catalog.
- **Distinguish actor identity from authority.** Record who initiates, who benefits or bears consequence, what authority is presented, and where permission is decided without treating role labels as authorization proof.
- **Source triggers and preconditions.** Separate external events, scheduled or system triggers, required business state, environmental assumptions, and setup performed by the use case itself.
- **Describe decisions and observable outcomes, not screen choreography.** Capture system responses, business branches, state transitions, and external effects while leaving layout and interaction detail to experience modeling.
- **Model alternatives by consequence.** Include denial, invalid input, conflict, timeout, duplicate request, partial effect, unavailable dependency, cancellation, and recovery only where reachable and material.
- **State guarantees at termination.** Define committed state, emitted or suppressed effects, user-visible outcome, audit or notification consequence, and what remains uncertain after success, rejection, or interruption.
- **Trace claims to acceptance and ownership.** Connect each material path to current rule or contract evidence, an observable acceptance oracle, and an owner for unresolved policy, data, permission, or integration behavior.

## Anti-Patterns

- Substitute a click sequence, component map, or implementation flow for actor goal and system guarantee.
- Model only the successful path or collapse rejected, failed, unknown, and compensated outcomes into one error branch.
- Invent preconditions, authority, defaults, or guarantees to make the narrative complete when source evidence is missing.

## Stop Conditions

Escalate when actor authority, business goal, system boundary, authoritative rule, consequential side effect, or termination guarantee is ambiguous. Also escalate when external owners cannot confirm a material path, or failure could affect money, permission, safety, regulated data, or irreversible operations.

## Output Contract

- bounded use-case model with actors and authority, trigger and preconditions, decision paths, state and side effects, termination guarantees, acceptance trace, unknowns, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | actor goal preconditions alternates failures or postconditions remain incomplete | accepted use case defines every material exit and guarantee | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | actor rule path or postcondition claims need current proof | current source tests contracts and owner artifacts prove each claim | analysis-agent | evidence-record, proof-limit, residual-risk |
| [fully dressed](references/fully-dressed-template.md) | template | a formal actor precondition postcondition and exception use-case artifact is required | the task only needs partial actor or scenario analysis | analysis-agent | completed-contract |
