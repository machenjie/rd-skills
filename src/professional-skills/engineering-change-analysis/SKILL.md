---
name: engineering-change-analysis
description: "Use `analysis-agent`: `implementation-preparation` for changes, `diagnosis-only` for verified cause, or `source-backed-answer` for repository questions. Skip source-free, Direct Task, and accepted-Brief narrow artifacts."
---

# engineering-change-analysis

## Role

Support `analysis-agent` in the selected source-backed mode. For Analyzed Work,
the current Engineering Brief is the only operational analysis authority;
Specialist work is input pending Brief incorporation.

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

## Professional Decision Rules

- Bind the selected mode to its `mode-contract`.
- Apply Core `task_contract.analyzed_work_authority` for initial closure,
  decision-invalidated Delta Analysis, transitive impact, and Skill routing.
- Prove its owner, impact, failure, validation, and proof limits.
- Put source-proven placement and Specialist results in the Brief.
- Route unresolved structural placement to `architecture-impact-reviewer`.
- Put a complete Task Contract v2 that Main can dispatch verbatim in the Brief,
  not a derived Task DAG or handoff.

## High-Value Gotchas

- Proximity is not ownership.

## Execution Checklist

1. Load the selected mode contract and triggered guidance.
2. Return its result and proof limit under Core.

## Stop / Escalation Conditions

- Stop for user decisions or result-invalidating gaps.
- Brief conflict or protected change returns `blocked`.
- Structural placement or dependency direction routes to `architecture-impact-reviewer`.
- Foundational invalidation permits full analysis.

## Output Contract

- mode result, source evidence, and proof limit
- implementation-preparation: authoritative Brief, dispatchable Slice, Specialist input

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
