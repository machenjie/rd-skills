---
name: business-invariant-analysis
description: "`analysis-agent`/`task-agent`/`review-agent`: use when changes may alter money, permissions, tenants, or audit rules; skip presentation-only work with unchanged invariants."
---

# business-invariant-analysis

## Registry Trigger

**Use when**

- a rule, status transition, entitlement, money movement, or tenant invariant changes
- the same business decision appears in SQL, controller, UI, job, or test code
- object or enforcement ownership is unclear

**Do not use when**

- the change is presentation-only and cannot alter business behavior
- the relevant invariant and owner are already explicit and unchanged

## Skill Role

Identify business invariants from current source and explicit owner evidence. Do not create a business corpus, generated semantic bundle, persistent state, or internal protocol.

## Inputs

- desired behavior and non-goals
- current source, tests, contracts, and owner evidence
- affected actors, objects, states, entry points, and side effects

## High-Value Rules

- Classify each material claim as verified fact, inference, assumption, or open question.
- Every rule needs an owner, enforcement point, entry points, failure behavior,
  and validation mapping.
- Every lifecycle needs allowed and forbidden transitions, actors, guards, and
  effective timing where relevant.
- Treat previous summaries as search leads only; current source or an explicit
  owner decision establishes the rule.
- Select one authoritative enforcement location where feasible and identify every credible bypass path.

## Anti-Patterns

- DTO shape and database schema do not by themselves define domain ownership.
- A happy-path example does not prove forbidden transitions.
- A refactor can change business semantics through ordering, defaults, or failure behavior.

## Execution Checklist

1. Define the business terms and owning objects used by this task.
2. Trace each rule across every mutation and decision entry point.
3. Record allowed, denied, and boundary cases with expected outcomes.
4. Identify the authoritative enforcement owner and rejected locations.
5. Map each material invariant to a test, review check, or explicit gap.

## Stop Conditions

- Stop when money, entitlement, permission, compliance, audit, irreversible data,
  or historical interpretation lacks an authoritative owner decision.
- Escalate when current sources disagree or an important bypass cannot be inspected.

## Output Contract

- vocabulary, owners, invariants, transitions, enforcement points, bypass paths,
  golden cases, source evidence, open questions, validation map, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [business invariant](references/business-invariant-checklist.md) | decision-checklist | domain vocabulary rule owner state transition or forbidden outcome remains unclear | the change is presentation-only with no business behavior | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
