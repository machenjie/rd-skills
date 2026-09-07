---
name: configuration-runtime-policy
description: "`analysis-agent`/`task-agent`/`review-agent`: use when typed config, defaults, flags, modes, rollout, rollback, or cleanup changes; skip when runtime policy is unaffected."
---

# configuration-runtime-policy

## Registry Trigger

**Use when**

- configuration runtime policy typed config default validation fail fast hot reload feature flag owner expiry cleanup kill switch stale flag mode kind switch tenant user experiment rollout rollback config observability

**Do not use when**

- no task-local configuration runtime policy decision is required

## Skill Role

Own typed, observable, reversible configuration; prevent invariant bypass.

## High-Value Rules

- Bind typed source, values, owner, default, precedence, apply boundary, and effective state.
- For protected invariants, use consequence-derived defaults, pre-effect validation, bounded variants, and atomic last-good recovery.
- Load only the named output Reference.

## Anti-Patterns

- Local success lacks configuration evidence.

## Stop Conditions

- Stop on invariant bypass or unsafe rollout/recovery.

## Output Contract

- Return a Configuration Policy: define scope, schema, defaults, fail-fast validation, flag lifecycle, kill/runtime-switch rationale, test matrix, cleanup owner, rollout, rollback, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Precedence, rollout, reload, or kill-switch mechanisms remain unsettled | The typed source and runtime behavior are unchanged | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Configuration affects defaults, variants, security, or cleanup lifecycle | No behavior-changing key, flag, or mode changes | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Config safety depends on fresh effective-state and variant validation | No default, rollout, or bounded-mode claim needs proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
