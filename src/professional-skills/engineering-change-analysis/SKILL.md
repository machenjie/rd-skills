---
name: engineering-change-analysis
description: "Use `analysis-agent`: `implementation-preparation` for changes, `diagnosis-only` for verified cause, or `source-backed-answer` for repository questions. Skip source-free, Direct Task, and accepted-Brief narrow artifacts."
---

# engineering-change-analysis

## Role

Support `analysis-agent` in one source-backed change, diagnosis, or answer mode.
Specialist owns unresolved placement. For
Analyzed Work, the current Engineering Brief is the only operational analysis
authority; Specialist work is input until Brief incorporation.

## When To Use

- implementation-preparation for source-backed desired-behavior, affected-consumer, and verification analysis before implementation or repair
- diagnosis-only for verified cause analysis
- source-backed-answer for a repository-dependent engineering question

## Do Not Use

- eligible bounded Direct Task
- source-free question
- accepted Engineering Brief already exists and the user explicitly requests one narrow artifact analysis
- module-boundary placement decision
- dependency-direction placement decision

## Required Inputs

- selected mode and mode-trigger evidence
- bounded source evidence and known constraints

## Professional Decision Rules

- Bind the dispatch to its selected mode and corresponding `mode-contract` Reference.
- Load supporting References independently when their own contracts trigger.
- In one pass, prove owner, invariants, impact, and proof limits.
- Do not invent user choices, repeat the scope, or cross modes.
- Map material behavior, consumers, contracts, data, failure, tests, release, observability, and docs.
- Put source-proven placement and triggered Specialist results in the Brief.
- Put a complete Task Contract v2 that Main can dispatch verbatim in the Brief,
  not a derived Task DAG or handoff.
- Use `refactoring` only after source proves its destination owner and placement.
- Route flagged structural risk with source evidence to `architecture-impact-reviewer` for placement, module-boundary, and dependency-direction decisions.

## High-Value Gotchas

- The nearest file may not own the rule; inspect same-pattern evidence without mode leakage.

## Execution Checklist

1. Classify the request into exactly one supported mode.
2. Load that mode contract and only task-triggered Layer 3 guidance.
3. Complete one mode result with its proof limit.

## Stop / Escalation Conditions

- Stop for an underived user decision or a gap that can invalidate the conclusion.
- Route structural-risk evidence to `architecture-impact-reviewer` with placement, module-boundary, and dependency-direction decisions left unresolved.
- Return Brief conflicts or protected-decision changes `blocked` through Main
  for analysis and redispatch.

## Output Contract

- selected mode result
- implementation-preparation: authoritative Brief with verbatim-dispatchable Slice and incorporated Specialist input
- source evidence and proof limit

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a concrete surface inventory across product, UX, domain, API, data, frontend, backend, integrations, security, tests, release, observability, and docs | Evidence freshness, consumer proof, or performance blast radius is the core risk | analysis-agent | checklist-result, residual-risk |
| [diagnosis only](references/diagnosis-only.md) | mode-contract | engineering change analysis selects diagnosis-only | engineering change analysis is executing another mode | analysis-agent | mode-result, proof-limit |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on changed-surface-to-validation mapping, same-pattern scan proof, consumer evidence, rollback limits, graph/report freshness, or proof limits | Only high-level routing is needed and evidence is not being closed | analysis-agent | evidence-record, proof-limit, residual-risk |
| [implementation preparation](references/implementation-preparation.md) | mode-contract | engineering change analysis selects implementation-preparation | engineering change analysis is executing another mode | analysis-agent | mode-result, proof-limit |
| [index](references/index.md) | index | competing engineering change analysis references require dependency, conflict, or output-fragment selection | the engineering change analysis root or a task-named reference already resolves selection | analysis-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | Performance/resource blast radius may include CPU, memory, network, disk, lock contention, throughput, or latency | No performance-sensitive path or resource tradeoff is material | analysis-agent | selected-approach, residual-risk |
| [source backed answer](references/source-backed-answer.md) | mode-contract | engineering change analysis selects source-backed-answer | engineering change analysis is executing another mode | analysis-agent | mode-result, proof-limit |
