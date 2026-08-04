---
name: change-documentation-gate
description: "Use `task-agent` to update source-backed documentation or `review-agent` to assess documentation impact and accuracy when public behavior or operator workflows change. Skip work with no audience-facing behavior change."
---

# change-documentation-gate

## Role

Support `task-agent` and `review-agent` for source-owned documentation accuracy,
migration guidance, and operator instructions.

- **Task mode (`task-agent`):** Apply the behavior delta to its owning documentation source.
- **Review mode (`review-agent`):** Judge published guidance against current behavior.

## When To Use

- public behavior or operator workflow changed
- documentation impact

## Do Not Use

- no audience facing change
- self review request

## Required Inputs

- changed behavior summary
- documentation scope
- **Task mode (`task-agent`):** owning documentation source, generated origin, and link, example, or command checks.
- **Review mode (`review-agent`):** changed guidance with behavior and freshness evidence.

## Professional Decision Rules

- Update documentation when behavior, public contract, configuration, operations, migration, deprecation, or user workflow changes.
- Keep examples executable and consistent with current names, defaults, errors, and version behavior.
- Place facts in the owning source document and link rather than duplicate unstable details.
- Validate links, commands, generated outputs, and migration instructions against the final implementation.

## High-Value Gotchas

- Stale examples are worse than missing examples.
- Generated docs must be changed at their source.
- A migration guide without rollback and version boundaries is incomplete.

## Execution Checklist

1. Trace the behavior delta to its audience, owning document, generated origin, and version boundary.
2. Choose update, migration note, deprecation guidance, or evidence-backed no-docs treatment.
3. Verify examples, commands, links, rollback guidance, and safe-disclosure boundaries.
4. **Task mode:** update the owning source for the accepted behavior delta.
5. **Review mode:** judge examples, commands, links, and migration guidance.
6. Stop closure when source behavior and published guidance cannot be reconciled.

## Stop / Escalation Conditions

- Stop release when changed audience behavior lacks documentation or a source-backed no-docs rationale.
- Stop no-docs decisions when affected audience, docs surface, source evidence, generated artifact, or behavior-delta proof is missing.
- Stop publishing when docs expose secrets, internal topology, tenant-sensitive details, unapproved security posture, or customer/audit data without safe-disclosure review.
- Stop migration, runbook, ADR, incident, compliance, or deprecation closure when owner, expected output, rollback, retention, approval, freshness, or validation evidence is implicit.

## Output Contract

- **Task mode (`task-agent`):** documentation changes; behavior mapping; residual documentation debt.
- **Review mode (`review-agent`):** documentation verdict; stale guidance findings; unproven audience behavior.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs quick artifact coverage across README, API docs, migration notes, ADRs, changelog, runbooks, user docs, config, and skipped rationale | Detailed output fields or evidence closure is required | task-agent, review-agent | checklist-result, residual-risk |
| [documentation output and gates](references/documentation-output-and-gates.md) | targeted | Drafting or reviewing documentation matrices, release notes, runbooks, migration notes, ADRs, incident/compliance packets, or no-docs decisions | Body output contract is sufficient for a small decision | task-agent, review-agent | gate-decision, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Closure depends on source-to-doc freshness, consumer-impact proof, rendered/link/spec validation, evidence retention, safe disclosure, or tool-output boundaries | No evidence freshness, retention, or safe-disclosure risk is material | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
| [index](references/index.md) | index | competing change documentation gate references require dependency, conflict, or output-fragment selection | the change documentation gate root or a task-named reference already resolves selection | task-agent, review-agent | reference-selection |
