---
name: engineering-change-analysis
description: "Use `analysis-agent` for implementation preparation, diagnosis, source-backed answers, or technical investigation. Skip already-decided implementation and questions fully answered by supplied facts."
---

# engineering-change-analysis

## Role

For `analysis-agent`, return one mode's source-backed read-only result.

## When To Use

- implementation-preparation when the user requests design or evidence leaves an important implementation decision unresolved
- diagnosis-only for verified cause analysis
- source-backed-answer for a repository-dependent engineering question
- technical-investigation for external facts, version compatibility, options, or feasibility

## Do Not Use

- implementation whose remaining unknowns are local owner, file, test, or caller discovery
- question fully answered by supplied facts
- accepted Engineering Brief already exists and the user explicitly requests one narrow artifact analysis
- module-boundary placement decision
- dependency-direction placement decision

## Required Inputs

- selected mode
- question, constraints, candidates, and available evidence
- repository evidence only when the question depends on a repository
- proof boundary

## Professional Decision Rules

- Load only the selected mode and active named References without preloading the index or switching modes.
- The selected reference supplies source proof, decisions, validation, and proof limits; do not create a formal contract without a real consumer.

## High-Value Gotchas

- Prior reports and nearby code are not current source ownership proof.

## Execution Checklist

1. Choose the analysis mode.
2. Separate source fact, supported inference, and unknown.
3. Prove repository ownership when the question depends on code.
4. Use target-version primary sources for external technical claims.
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
| [technical investigation](references/technical-investigation.md) | mode-contract | Technical investigation needs external facts version compatibility or option comparison | Implementation is already decided or the question is answered by supplied facts | analysis-agent | mode-result, proof-limit |
| [feasibility experiment design](references/feasibility-experiment-design.md) | targeted | A technical uncertainty needs a falsifiable bounded experiment | Existing evidence resolves the question without an experiment | analysis-agent | decision-record, validation-plan, proof-limit |
