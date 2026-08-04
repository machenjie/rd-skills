---
name: version-compatibility
description: "`analysis-agent`/`task-agent`/`review-agent`: use when API, schema, event, or behavior changes need compatibility, deprecation, rollout, or migration; skip without version impact."
---

# version-compatibility

## Registry Trigger

**Use when**

- assess backward compatibility deprecation version negotiation and client migration

**Do not use when**

- no task-local version compatibility decision is required

## Skill Role

Define consumers, compatibility dimensions, mixed-version behavior, retirement, rollback readability, and evidence. Exclude contract design, migration execution, and release authority.

## High-Value Rules

- **Inventory evidence-backed consumers and skew.** Include services, installed clients, partners, events, stored data, caches, jobs, scripts, libraries, and rollback versions.
- **Classify compatibility by behavior.** Evaluate source, binary, wire, schema, persisted-data, config, operational, and semantic compatibility; additive changes can break strict consumers.
- **Design mixed-version coexistence.** Define old/new writer-reader behavior, defaults, unknown values, ordering, activation, and partial rollout from the observed upgrade boundary.
- **Select migration from constraints.** Compare versioning, negotiation, additive bridge, dual read/write, expand-contract, translation, and coordinated cutover without a universal sequence.
- **Treat errors, defaults, enums, and timing as contract.** Check retry/timeout meaning, error shape, new values, omissions, activation order, and schema-invisible behavior.
- **Make retirement evidence-based.** Name usage signals, owner, deprecation communication, residual stored data or messages, and the removal condition.
- **Preserve rollback readability.** Show whether old code safely reads and acts on new state and side effects; otherwise define exposure limits and forward-repair ownership.

## Anti-Patterns

- Assuming consumers upgrade together or deriving their window from producer speed.
- Calling added fields non-breaking despite changed defaults, validation, matching, or behavior.
- Removing a bridge by calendar without usage, stored-data, queue, and rollback evidence.

## Stop Conditions

Escalate when consumers or skew are unknown, versions cannot coexist, rollback cannot interpret new state, long-lived clients lack adoption, or retirement evidence is unavailable. Also escalate when compatibility affects public, regulated, financial, permission, or irreversible behavior.

## Output Contract

- compatibility decision with consumer inventory, compatibility dimensions, mixed-version matrix, migration mechanism, retirement evidence, rollback limits, proof gaps, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | mixed-version failures lack negative-path coverage | compatibility tests cover triggered boundaries | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [compatibility benchmarks](references/compatibility-benchmarks.md) | benchmark-pattern | migration policy remains unresolved | no mixed-version consumers are affected | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | consumer evidence may be stale | current artifacts prove consumer behavior | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
