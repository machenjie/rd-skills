---
name: engineering-change-analysis
description: "Use `analysis-agent`: `implementation-preparation` for changes, `diagnosis-only` for verified cause, or `source-backed-answer` for repository questions. Skip source-free, Direct Task, and accepted-Brief narrow artifacts."
---

# engineering-change-analysis

## Role

For `analysis-agent`, this root owns mode choice, evidence trust, read-only scope,
and the no-reroute boundary; the mode contract owns output.

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

- selected mode
- bounded source evidence and constraints
- proof boundary

## Professional Decision Rules

- Load exactly the selected mode contract and only active named References.
- Never preload the index.
- Separate source fact, supported inference, and unknown.
- Prove ownership or placement from current source rather than proximity.
- Keep Professional, Layer3, and mode fixed; never reroute.
- Keep Core analyzed authority fixed; never create parallel authority.

## High-Value Gotchas

- Prior reports and nearby code are not current source ownership proof.

## Execution Checklist

1. Confirm mode, evidence boundary, and current source.
2. Return the mode contract's result, validation, and proof limits.

## Stop / Escalation Conditions

- A mode conflict, user choice, or result-invalidating gap returns `blocked`
  without changing mode or route.

## Output Contract

- The selected mode contract's result, source evidence, and proof limit.

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
