---
name: repository-impact-inspection
description: "`analysis-agent`/`task-agent`/`review-agent`: use after a candidate owner/change surface is known and consumers, tests, contracts, or generated impact need bounded proof."
---

# repository-impact-inspection

## Registry Trigger

**Use when**

- candidate owner and change surface are known but affected consumers tests contracts configuration docs or generated surfaces need proof
- a cross-module or public-contract change needs a bounded evidence-backed impact map

**Do not use when**

- a local owner and its adjacent tests fully establish the change boundary
- the task asks for a high-level answer with no repository-specific claim
- source of truth candidate owner or change surface is still unknown; use `repository-context-map` first

## Skill Role

Inspect the known owner and change surface; trace affected consumers, tests, contracts, configuration, documentation, and generated outputs through native search and direct reads.

## Inputs

- bounded question, candidate owner, and change surface
- repository read/search access
- known contracts, generated paths, and test entry points

## High-Value Rules

- Require source-of-truth and candidate owner/change evidence from `repository-context-map` or equivalent direct inspection.
- From that candidate, follow imports, calls, references, tests,
  configuration, docs, and generated-source markers only as needed.
- Distinguish direct evidence, inferred impact, and uninspected scope.
- Treat generated output as non-editable until its source is identified.
- Stop expanding when each material acceptance and risk has an owner and proof path.

## Anti-Patterns

- Directory names are not ownership evidence.
- Search hits can be consumers, examples, dead code, or generated output.
- Absence of a reference hit is not proof of no dynamic consumer.

## Execution Checklist

1. Confirm the supplied candidate owner, change surface, and source of truth.
2. Search symbols, contracts, configuration keys, and generated markers.
3. Classify direct owner, consumer, test, config, docs, and generated paths.
4. Record affected and uninspected consumers, tests, contracts, and generated surfaces.
5. Return the smallest sufficient impact map and validation boundary.

## Stop Conditions

- Stop when further search cannot change impact scope or validation.
- Route missing source-of-truth, candidate-owner, or change-surface discovery to `repository-context-map`.
- Escalate when dynamic ownership, unavailable dependencies, or generated tooling
  prevents a safe impact conclusion.

## Output Contract

- candidate owner and change-surface binding, affected consumers, tests, contracts,
  configuration, docs, generated boundaries, validation boundary, uninspected scope, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [repository impact](references/repository-impact-checklist.md) | decision-checklist | owners callers consumers tests configuration generated artifacts or public contracts remain unclear | the local owner and adjacent tests fully bound the impact | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
