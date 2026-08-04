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

Define configuration as a typed, observable, reversible policy boundary. Prevent flags, modes, and overrides from becoming invariant bypasses, hidden strategy systems, or stale rollout mechanisms.

## High-Value Rules

- Define each configurable behavior's schema, values, owner, default, precedence, and read boundary from current source of truth.
- Select consequence-derived defaults that fail closed unless an approved degradation design preserves protected invariants.
- Reject invalid configuration before effect unless the selected degradation, alert, and rollback behavior is explicitly safe.
- Reject switches that bypass domain, permission, tenant, transaction, encryption, audit, or compliance invariants.
- Bound flags, modes, providers, and strategies by explicit semantics, owner, lifecycle, telemetry, and old/new behavior proof; avoid hidden registries.
- When hot reload is required, validate before atomic publication and preserve current-state visibility and recovery to a known-good version.
- Map config-driven wiring to affected source and validation, and require an owned cleanup decision for temporary configuration.

## Anti-Patterns

- Treating build-, deploy-, and runtime-time configuration as interchangeable hides when behavior can change.
- Leaving precedence implicit makes code, file, environment, CLI, remote, tenant, experiment, and operator values nondeterministic.
- Using test-friendly defaults in production silently changes safety behavior.
- Publishing hot reloads before validation exposes partial or invalid state.
- Creating untyped or ownerless flags leaves obsolete branches and unverifiable rollout state.
- Packing unrelated strategies into one mode parameter creates an unbounded policy registry.

## Stop Conditions

- Untyped config stale flags and vague mode switches bypass invariants create hidden strategy systems and make rollout rollback unsafe

## Output Contract

- Return a Configuration Policy: define scope, schema, defaults, fail-fast validation, flag lifecycle, kill/runtime-switch rationale, test matrix, cleanup owner, rollout, rollback, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Precedence, rollout, reload, or kill-switch mechanisms remain unsettled | The typed source and runtime behavior are unchanged | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Configuration affects defaults, variants, security, or cleanup lifecycle | No behavior-changing key, flag, or mode changes | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Config safety depends on fresh effective-state and variant validation | No default, rollout, or bounded-mode claim needs proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
