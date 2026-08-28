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
- A comparison missing its baseline or treatment is incomplete, has no evidence class, and supports no efficacy claim.
- A complete structural baseline/treatment comparison with live behavior not collected has evidence class `structural_only` and final verdict `not_enough_evidence`.
- A valid complete live comparison has evidence class `live_agent` and uses the Core behavior-evaluation verdict mapping.
- Define each benchmark's task, baseline, treatment, metrics, verdict, caveats, and reproducible input boundary.
- Measure token and turn overhead or record them as not collected rather than omitting the limitation.
- Separate structural fixture validation from empirical agent behavior when stating what the evidence proves.
- Classify changed Skill, Profile, routing, reference, validation, and benchmark surfaces as behavioral unless current evidence proves docs-only impact.

## Anti-Patterns

- A benchmark can be useful even when overhead is `not_collected`; the caveat must be explicit.
- A structural fixture validates schema and evaluation plumbing, not live agent productivity.
- The unit of comparison is the same task under baseline and treatment conditions.
- A reference treatment without an explicit required allow-list is unbounded and invalid.
- Blind bindings, metrics, directions, evidence classes, or verdicts not derived from Core are invalid.
- A packet that co-locates the oracle, observations, verifier-owned captures, or post-capture reveal, or binds opaque arms differently, is invalid.
- Capture metadata is not live evidence without capture bytes, digest, ordered baseline/candidate source identity, provenance, and controlled-binding agreement.
- Aggregate averages cannot override a per-case NEW regression.
- `structural-only` is an evidence class; missing live behavior has final verdict `not_enough_evidence`, while a valid nondiscriminating live comparison is `no_effect`.
- A lower-cost treatment with any routing, Review, or code-quality regression is `regression`; cost never overrides correctness.
- Benchmark reports should name what changed, what improved, what did not, and what remains unmeasured.

## Stop Conditions

- Escalate when a change makes an empirical efficacy claim without baseline/treatment data.
- Escalate when a fixture passes by matching keywords but does not test the professional behavior claimed.
- Escalate when token or turn overhead is omitted.
- Escalate when a benchmark omits over-routing or under-routing risk.
- Escalate when benchmark data includes raw prompts, secrets, user-specific source material, or unbounded command output.

## Output Contract

- Return a Skill Efficacy Benchmark: evidence class, available baseline/treatment comparison, metrics, token/turn overhead, routing errors, final verdict, caveats, and regression command

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | treatment and baseline agent behavior need a comparable benchmark design | no Skill efficacy comparison or behavior benchmark is requested | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | an efficacy evaluation needs routing behavior pressure and regression coverage | the benchmark design and required coverage are already fixed | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | an efficacy assertion requires reproducible treatment baseline and negative-control proof | no comparative Skill efficacy claim will be made | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
