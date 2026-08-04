---
name: user-role-identification
description: "`analysis-agent`/`task-agent`/`review-agent`: use when actors, personas, admins, customers, service accounts, or role risks need identification; skip when roles are unchanged."
---

# user-role-identification

## Registry Trigger

**Use when**

- identify actors personas operators administrators customers and service accounts

**Do not use when**

- no task-local user role identification decision is required

## Skill Role

Identify actors and authority only to the depth required by affected behavior, risk, and downstream decisions.

## High-Value Rules

- Classify affected actors with authority-specific labels rather than generic "user" or "internal" labels.
- When support, operator, job, callback, or external-system paths can affect the flow, inspect those actors even if the request names only an end user.
- Separate persona context from authorization, data scope, business authority, audit, and denied-action decisions.
- Define affected object, field, tenant, export, and related-record visibility, including denied scope, at the enforcement boundary.
- Require owner, scope, credential lifecycle, audit, and least-privilege evidence for machine actors, and explicit authority for privileged overrides.
- Refresh prior role evidence against current source and change scope before using it to drive permission, workflow, or test decisions.

## Anti-Patterns

- **Role inventories are source-of-truth inputs, not implementation proof.** Use them without treating them as enforcement evidence.
- **Data visibility must include negative visibility.** Explicitly name data, fields, tenants, exports, aggregates, and related records the actor cannot access.
- **Machine actors have blast radius.** A leaked credential or flawed worker can bypass UI, sessions, and human approval. Scope and audit them as rigorously as human roles.
- **Support/admin exceptions are product and compliance decisions.** If an override is needed, name the invariant exception, approval path, audit event, and downstream validation.

## Stop Conditions

Escalate when an actor crosses tenant or ownership boundaries, or can read or export regulated, financial, private, or cross-actor data. Also escalate when an actor can mutate money, legal, compliance, identity, subscription, deletion, or role-grant state, or can impersonate or elevate. Escalate when an actor uses a broad service account, depends on unsigned external claims, or relies on stale evidence, UI-only filtering, or internal-system trust without current-source proof.

## Output Contract

- role inventory with responsibilities permissions and affected journeys

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | human machine support or external actor boundaries remain ambiguous | current policy uniquely defines every affected actor class | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects roles authority visibility tenants machines or external actors | no actor authority or data-visibility boundary changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | role scope trust or tenant claims need fresh proof | current policies entry points and tests prove each claim | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
