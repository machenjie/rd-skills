---
name: agent-tool-permission-sandbox
description: "`analysis-agent`/`task-agent`/`review-agent`: classify command risk when targets, mutation, recovery, effects, or authorization are unresolved; skip when facts are current."
---

# agent-tool-permission-sandbox

## Registry Trigger

**Use when**

- a concrete command or operation has unresolved targets or mutation surfaces
- reversibility, recovery, external effects, capability facts, or authorization facts need task-level classification

**Do not use when**

- every command-risk fact is current and unambiguous
- the task is defining or changing runtime authority or host enforcement

## Skill Role

Classify one proposed command or operation from task-local facts. Consume
capability and authorization facts from their existing owners without redefining
them.

## Inputs

- exact command or operation and available target-resolution evidence
- task-local scope, affected resources, and possible indirect mutations
- current capability facts and authorization facts from their owners
- reversibility, recovery, external-effect, and ambiguity evidence

## High-Value Rules

- Verify the exact target from arguments, configuration, environment, selectors, and runtime discovery.
- Map the mutation surface across local resources, persistent data, subprocesses, generated outputs, and remote systems.
- Classify reversibility from whether the original state can be restored. Name the recovery mechanism and its evidence separately.
- Inspect external effects such as requests, service changes, messages, billing, or data disclosure.
- Record capability facts and authorization facts as supplied. Mark missing or conflicting facts unknown instead of inferring a grant.
- Preserve unresolved ambiguity for expansions, transitive tools, hooks, callbacks, and dynamically selected targets.

## Anti-Patterns

- A read-named command can still change metadata, caches, subprocesses, or remote state.
- A reversible local edit is not recoverable without a proven recovery mechanism.
- No local file change does not imply that no external effect occurred.
- Capability does not prove authorization, and authorization does not resolve side effects.

## Execution Checklist

1. Resolve the exact target and every selector that can expand it.
2. Enumerate the direct and indirect mutation surface.
3. Separate reversibility from the available recovery mechanism.
4. Record external effects and affected resources.
5. Attach current capability and authorization facts without changing their meaning.
6. Return every unresolved ambiguity and its consequence.

## Stop Conditions

- Return an unresolved decision when the exact target, mutation surface, recovery, or external effects cannot be bounded.
- Identify the existing owner of a missing capability or authorization fact without defining a new grant or host control.

## Output Contract

- task-level command risk decision with exact target, mutation surface, reversibility and recovery, external effects, capability facts, authorization facts, unresolved ambiguity, and residual risk

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [profile permission](references/profile-permission-checklist.md) | decision-checklist | target mutation recovery external-effect capability or authorization facts remain unresolved | every command-risk field is current and supported | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
