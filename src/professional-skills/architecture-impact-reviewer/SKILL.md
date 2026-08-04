---
name: architecture-impact-reviewer
description: "Use `analysis-agent` for module-boundary or dependency-direction analysis, or `review-agent` for independent assessment of a bounded architecture artifact. Skip isolated owner-internal edits with no structural impact."
---

# architecture-impact-reviewer

## Role

Support `analysis-agent` and `review-agent` for bounded structure, dependency, ownership, reuse, and scalability decisions.

- **Analysis mode (`analysis-agent`):** Decide placement, ownership, and dependency direction.
- **Review mode (`review-agent`):** Judge the artifact against its placement and boundary criteria.

## When To Use

- module boundary change
- dependency direction risk
- owner-internal implementation structure reuse or deliberate separation remains unresolved

## Do Not Use

- isolated owner internal edit after placement is fixed
- no structural impact

## Required Inputs

- desired behavior
- module and dependency boundary
- **Analysis mode (`analysis-agent`):** candidate ownership, dependency, consumer, and reuse evidence.
- **Review mode (`review-agent`):** bounded architecture artifact with its placement criteria and supporting evidence.

## Professional Decision Rules

- When new structure or a boundary is proposed, place behavior with the owner of its reason to change and preserve the affected dependency direction.
- Reuse an abstraction only when its contract and ownership match current evidence.
- Similarity alone does not justify reuse.
- Skip reuse proof for owner-internal edits without structural change.
- Compare the smallest local design with broader alternatives using only material change-locality, coupling, compatibility, operability, and deletion constraints.
- Require placement and ownership rationale only for proposed files, services, shared helpers, dependencies, public surfaces, or moved responsibilities that change structure.

## High-Value Gotchas

- A shared helper without one owner becomes a coupling sink.
- New abstraction before a second concrete use often raises change cost.
- Generated output is not the source of truth.

## Execution Checklist

1. Trace the proposed responsibility to its current owner, consumers, and dependency direction.
2. Compare the smallest local placement with only materially different structural alternatives.
3. Verify compatibility, reversibility, deletion cost, and affected enforcement boundaries.
4. **Analysis mode:** select one placement and record rejected alternatives.
5. **Review mode:** judge placement, dependency direction, and enforcement boundaries.
6. Stop when ownership, consumer, or dependency evidence cannot support one placement.

## Stop / Escalation Conditions

- Stop an architecture decision when a proposed structure or boundary lacks the applicable owner, public/private surface, dependency direction, data ownership, reversibility, or simpler-alternative evidence.
- Stop new shared abstractions, plugins, services, queues, registries, or generic interfaces until current consumers, owner, reversibility, and rejected local alternative are proven.
- Stop public or indirectly consumed boundary changes when affected-consumer and compatibility or versioning proof is missing. Topology, enforcement, rollout, or observability proof becomes required only for runtime, deployment, ownership, or dependency-direction changes.
- Stop tool execution when graph tooling, production telemetry, external connectors, or release actions lack permission/sandbox, scope, rollback/revert path, and redaction evidence.

## Output Contract

- **Analysis mode (`analysis-agent`):** placement decision; rejected alternatives; dependency and consumer impact.
- **Review mode (`review-agent`):** architecture verdict; boundary findings; unreviewed structural risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [architecture output and gates](references/architecture-output-and-gates.md) | targeted | L3-L5 analysis or review needs mode-specific closure and targeted gates for selected placement, consumer/data, topology/enforcement, or reversibility risk | The root result is sufficient and no selected risk needs the extended proof contract | analysis-agent, review-agent | gate-decision, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | A bounded L2 mode needs compact checks for its triggered placement, ownership, dependency, consumer, data, topology, or reversibility risk | The root contract is enough or targeted proof fields are required | analysis-agent, review-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing architecture impact reviewer references require dependency, conflict, or output-fragment selection | the architecture impact reviewer root or a task-named reference already resolves selection | analysis-agent, review-agent | reference-selection |
| [solution optimality](references/solution-optimality.md) | targeted | An architecture boundary, ownership, dependency, topology, or operational-responsibility decision has a material alternative | The change is owner-internal with no structural impact or current evidence already fixes placement | analysis-agent, review-agent | selected-approach, residual-risk |
