---
name: acceptance-criteria-builder
description: "Define source-backed, measurable acceptance with `analysis-agent` when acceptance is vague or failure behavior is unspecified. Do not select it when acceptance is already measurable or the request is question-only."
---

# acceptance-criteria-builder

## Role

Support `analysis-agent` in turning ambiguous intent into observable acceptance
for each affected actor, state, failure path, and preserved behavior.

## When To Use

- acceptance is vague
- failure behavior unspecified

## Do Not Use

- acceptance already measurable
- question only

## Required Inputs

- intent slice
- source evidence
- known constraints

## Professional Decision Rules

- Define acceptance as observable behavior, not implementation shape.
- Cover happy path, denied or invalid input, failure behavior, recovery, and preserved behavior.
- Map each material criterion to a realistic validation signal and state its proof limit.
- Keep non-goals explicit so tests do not silently expand scope.

## High-Value Gotchas

- “Tests pass” is evidence, not product acceptance.
- Implementation details can overconstrain a valid solution.
- Omitted negative and recovery paths create false completion.

## Execution Checklist

1. Trace every affected actor, trigger, precondition, outcome, and preserved behavior to source evidence.
2. Choose criteria granularity that constrains behavior without prescribing implementation.
3. Map each criterion to an observable validation signal and an explicit proof limit.
4. Stop drafting when evidence cannot distinguish a product choice from a source fact.

## Stop / Escalation Conditions

- Stop criteria drafting when actor, trigger, state, boundary, source requirement, verification method, or rejection condition is implicit.
- Stop implementation when criteria use vague success words without observable thresholds or test steps.
- Stop approval when permission, tenant, ownership, security, migration, async, rollback, accessibility, experiment, or non-functional paths lack negative and edge criteria.
- Escalate when required production data, compliance evidence, telemetry, stakeholder sign-off, or connector context cannot be inspected through authorized read/search access.

- Escalate when criteria require PII-bearing data or production-only conditions that cannot be replicated in test.
- Escalate when criteria involve regulatory compliance (GDPR, SOC 2, PCI-DSS, HIPAA) and need compliance team acceptance.
- Escalate when criteria are disputed between stakeholders.
- Never resolve stakeholder disputes silently.
- Escalate when a non-functional threshold requires load testing, benchmarking, or external security assessment.
- Escalate when proposed criteria conflict with another active change to the same contract or system boundary.
- Escalate when an experiment has no primary metric, no guardrails, no exposure event, unstable assignment unit, or no rule for sample ratio mismatch.

## Output Contract

- measurable acceptance
- non-goals
- proof expectations

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 draft or review needs a compact coverage check for actor, precondition, action, result, normal, invalid, boundary, permission, regression, compatibility, and evidence | The body quality gate is enough or evidence mapping/sign-off freshness is material | analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on criteria-to-validation mapping, stakeholder sign-off freshness, manual/audit evidence limits, or accepted residual risk | No criterion needs proof beyond the body evidence contract and quality gate | analysis-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing acceptance criteria builder references require dependency, conflict, or output-fragment selection | the acceptance criteria builder root or a task-named reference already resolves selection | analysis-agent | reference-selection |
