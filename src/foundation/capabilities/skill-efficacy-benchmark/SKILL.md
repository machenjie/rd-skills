---
name: skill-efficacy-benchmark
description: "`analysis-agent`/`task-agent`/`review-agent`: use when Skill changes need baseline/treatment evidence for routing, defects, or regressions; skip without an efficacy claim."
---

# skill-efficacy-benchmark

## Registry Trigger

**Use when**

- skill efficacy benchmark baseline treatment agent behavior improvement claim routing quality evidence quality review defects token overhead turn overhead over routing under routing
- eval fixture professional benchmark skill benchmark no baseline unsupported efficacy claim skill authoring validation behavior regression

**Do not use when**

- no task-local skill efficacy benchmark decision is required

## Skill Role

Evaluate whether a Skill, Profile, route, Reference, or benchmark improves agent behavior. Compare the same task under baseline and treatment using defects, routing, evidence quality, and overhead.

## High-Value Rules

- Reject real-world efficacy claims without representative baseline and treatment evidence for the same task.
- Classify missing-baseline evidence as `structural-only` with final verdict `not_enough_evidence` and no empirical or real-world efficacy claim.
- Define each benchmark's task, baseline, treatment, metrics, verdict, caveats, and reproducible input boundary.
- Measure token and turn overhead or record them as not collected rather than omitting the limitation.
- Separate structural fixture validation from empirical agent behavior when stating what the evidence proves.
- Measure over-routing and under-routing risk as well as selected-task success.
- When references form the treatment, select an explicit required allow-list and reject an unbounded catalog treatment.
- Classify changed Skill, Profile, routing, reference, validation, and benchmark surfaces as behavioral unless current evidence proves docs-only impact.

## Anti-Patterns

- A benchmark can be useful even when overhead is `not_collected`; the caveat must be explicit.
- A structural fixture validates schema and evaluation plumbing, not live agent productivity.
- The unit of comparison is the same task under baseline and treatment conditions.
- `structural-only` is an evidence class; missing baseline has final verdict `not_enough_evidence`, while `unknown` requires a valid but nondiscriminating comparison.
- Benchmark reports should name what changed, what improved, what did not, and what remains unmeasured.

## Stop Conditions

- Escalate when a change makes an empirical efficacy claim without baseline/treatment data.
- Escalate when a fixture passes by matching keywords but does not test the professional behavior claimed.
- Escalate when token or turn overhead is omitted.
- Escalate when routing improvements hide over-routing drag or under-routing safety gaps.
- Escalate when benchmark data includes raw prompts, secrets, user-specific source material, or unbounded command output.

## Output Contract

- Return a Skill Efficacy Benchmark: evidence class, available baseline/treatment comparison, metrics, token/turn overhead, routing errors, final verdict, caveats, and regression command

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | treatment and baseline agent behavior need a comparable benchmark design | no Skill efficacy comparison or behavior benchmark is requested | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | an efficacy evaluation needs routing behavior pressure and regression coverage | the benchmark design and required coverage are already fixed | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | an efficacy assertion requires reproducible treatment baseline and negative-control proof | no comparative Skill efficacy claim will be made | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
