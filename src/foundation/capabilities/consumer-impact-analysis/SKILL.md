---
name: consumer-impact-analysis
description: "`analysis-agent`/`task-agent`/`review-agent`: use when API, SDK, schema, event, package, CLI, or export changes may affect consumers; skip when no consumer contract can change."
---

# consumer-impact-analysis

## Registry Trigger

**Use when**

- consumer impact analysis API SDK schema event public export generated client mobile web backend consumer compatibility migration deprecation telemetry rollout rollback unknown consumer risk

**Do not use when**

- no task-local consumer impact analysis decision is required

## Skill Role

Establish known and unknown consumers of a changed contract, then select compatibility, migration, rollout, and validation from current evidence.

## High-Value Rules

- Own surface, consumers, compatibility/migration/rollout/rollback, and risk.
- Bound absence/readiness/deprecation/removal to current evidence; retain unknown external risk.
- Load only the active decision's named Reference.

## Anti-Patterns

- Local success substituted for evidence of the consumer impact analysis contract.

## Stop Conditions

Route contract, delivery/removal, sensitive scope, and proof gaps to their contract, `delivery-release-gate`, `security-privacy-gate`, and `quality-test-gate` owners. Stop on unowned external risk.

## Output Contract

- Return a Consumer Impact Report: changed contracts, consumers, compatibility, migration, deprecation, telemetry, rollout, rollback, tests, docs, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Compatibility, migration, telemetry, or mixed-version strategies compete | The private surface has no external or generated consumers | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Consumer impact spans SDKs, events, mobile clients, or unknown callers | No observable contract or public export changes | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Compatibility claims require fresh consumer, telemetry, or generated-artifact proof | No consumer-readiness claim is being approved | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
