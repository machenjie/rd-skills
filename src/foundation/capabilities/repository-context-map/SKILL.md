---
name: repository-context-map
description: "`analysis-agent`/`task-agent`/`review-agent`: discover source of truth, candidate owner, and change surface before planning; hand known candidates to impact inspection."
---

# repository-context-map

## Registry Trigger

**Use when**

- repository context map before planning discovers source of truth candidate owner change surface conventions and source generated boundary
- plan before repository inspection wrong placement missing call graph no repo map unfamiliar codebase registry profile and build artifacts skill authoring

**Do not use when**

- no task-local repository context map decision is required
- candidate owner and change surface are known and only consumer test contract or generated impact proof remains; use `repository-impact-inspection`

## Skill Role

Discover the minimum pre-plan repository context that identifies source of truth, candidate owner, change surface, conventions, generated boundaries, and remaining unknowns. Bounded impact proof remains outside this phase.

## High-Value Rules

- Before planning, use bounded repository searches and direct reads to inspect only enough source, registry, generated-boundary, and convention evidence to identify the source of truth, candidate owner, and change surface.
- Use a supplied exact path, symbol, or owner to prioritize the first direct read rather than establish ownership.
- End discovery when current source confirms the relevant owning or change role.
- Once a candidate owner and change surface are known, hand consumer, test, contract, configuration, documentation, and generated-impact proof to `repository-impact-inspection`.
- Mark unknown ownership or uninspected boundaries as `FACT`, `INFERENCE`, `ASSUMPTION`, or `OPEN QUESTION` with a next investigation owner; unknown is not safe.
- Separate source authoring content from generated built content and installed artifacts.
- Do not treat the context map as completion evidence.

## Anti-Patterns

- A repository map is not a broad inventory. It is the smallest evidence set that makes the plan reviewable.
- Generated outputs are impact surfaces, not automatically sources of truth.
- Tests, docs, and context freshness are part of the map because stale evidence and stale reader guidance cause false completion.
- Stale graph, missing graph edge, or graph/source mismatch requires graph refresh or explicit direct-source fallback.

## Stop Conditions

- Return through Main to `architecture-impact-reviewer` only when the authoring source, generator, generation authority, or module dependency remains unknown after a bounded generated-artifact trace, or current source reveals a material contradiction.
- Escalate to `quality-test-gate` when changed-code-to-test mapping is unclear or affected-test selection may miss dependents.
- Escalate to `security-privacy-gate` when the mapped area touches auth, secrets, permissions, user data, external input, or tool execution.
- Escalate deployment, install, build, migration, or packaging surfaces to `delivery-release-gate`.
- Block planning when the runtime source of truth cannot be found.

## Output Contract

- Return a Repository Context Map: inspected files and searches, source of truth, candidate owner, change surface, conventions, generated boundaries, unknowns, evidence limits, and impact-inspection handoff

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [task context evidence map](references/task-context-evidence-map.md) | evidence-pattern | source of truth candidate owner change surface or pre-plan context remains unclear | the candidate owner and change surface are known and only bounded impact proof remains | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [source generated boundary map](references/source-generated-boundary-map.md) | targeted | source generated artifact and authority boundaries are unclear | the authoritative source and regeneration path are explicit | analysis-agent, task-agent, review-agent | boundary-decision, residual-risk |
| [validation freshness handoff](references/validation-freshness-handoff.md) | targeted | validation predates the latest edit or must be transferred across an agent handoff | validation follows the latest edit and no handoff boundary exists | analysis-agent, task-agent, review-agent | validation-plan, proof-limit |
