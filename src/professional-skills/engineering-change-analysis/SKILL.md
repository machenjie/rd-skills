---
name: engineering-change-analysis
description: "`analysis-agent`: source-backed `implementation-preparation`, causal `diagnosis-only`, or repository `source-backed-answer`; skip source-free, implementation-ready, or accepted-artifact work."
---

# engineering-change-analysis

## Role

For `analysis-agent`, return one mode's source-backed read-only result.

## When To Use

- implementation-preparation for source-backed desired-behavior, affected-consumer, and verification analysis before implementation or repair
- diagnosis-only for verified cause analysis
- source-backed-answer for a repository-dependent engineering question

## Do Not Use

- bounded implementation-ready change whose owner, behavior, and verification are established
- source-free question
- accepted Engineering Brief already exists and the user explicitly requests one narrow artifact analysis
- module-boundary placement decision
- dependency-direction placement decision

## Required Inputs

- selected mode
- bounded source evidence and constraints
- proof boundary

## Professional Decision Rules

- Load only the selected mode and active named References without preloading the index or switching modes.
- Apply the `analysis-agent` Profile and Core contracts while consuming the bound Runtime selection receipt.
- The selected mode contract owns mode-specific source proof, decisions, output, stop conditions, and Proof Limits.

## High-Value Gotchas

- Prior reports and nearby code are not current source ownership proof.

## Execution Checklist

1. Choose the analysis mode.
2. Separate source fact, supported inference, and unknown.
3. Prove ownership from current source rather than proximity.
4. Establish placement from the current dependency graph.
5. Treat earlier reports and generated graphs as selectors until current source confirms their claims.
6. Return the selected mode contract's result with validation and explicit Proof Limits.

## Stop / Escalation Conditions

- After Core evidence closure, stop only when a mode conflict, user-owned choice, or gap invalidates the result.

## Output Contract

- Return the selected mode result with source evidence and Proof Limits.

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
