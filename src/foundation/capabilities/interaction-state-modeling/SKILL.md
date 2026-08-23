---
name: interaction-state-modeling
description: "`analysis-agent`/`task-agent`/`review-agent`: use when loading, empty, error, success, disabled, timeout, or permission states change; skip when visible state is unaffected."
---

# interaction-state-modeling

## Registry Trigger

**Use when**

- model empty loading error success disabled focused and permission states

**Do not use when**

- no task-local interaction state modeling decision is required

## Skill Role

Own states, transitions, recovery, accessibility signals, and evidence; exclude backend lifecycle and authorization policy.

## High-Value Rules

- Derive task-relevant observable states from current product and operation semantics.
- Keep unknown, partial, optimistic, and durable outcomes distinct until authority and reconciliation evidence close them.
- Load only the named state family whose decision problem is active.

## Anti-Patterns

- Do not substitute local success or a transport result for authoritative interaction-state evidence.

## Stop Conditions

Stop on unknown outcome or authority, unsafe repeat, data-losing recovery, unowned completion, unordered response, or unverified accessible recovery.

## Output Contract

- interaction-state decision with authoritative state mapping, transitions, uncertainty, available actions, optimistic and asynchronous behavior, accessibility signals, forbidden states, evidence limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [state semantics benchmark anchors](references/state-semantics-benchmark-anchors.md) | benchmark-pattern | State semantics need benchmark anchors from current operation and product evidence | Current operation semantics already fix the observable state distinctions | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [state distinction and outcome](references/state-distinction-and-outcome-patterns.md) | benchmark-pattern | Unknown, partial, optimistic, or durable outcomes need comparison | Current authority already fixes outcome distinctions and user actions | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [state derivation and recovery decisions](references/state-derivation-and-recovery-decisions.md) | targeted | State derivation, retry, cancellation, or recovery decisions remain open | Current backend contract fixes transitions, repeat safety, and recovery | analysis-agent, task-agent, review-agent | decision-record, failure-decision, residual-risk |
| [state transition and backend evidence](references/state-transition-and-backend-evidence.md) | evidence-pattern | Transition or backend-alignment claims need current evidence | No transition or backend-alignment claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [state accessibility evidence](references/state-accessibility-evidence.md) | evidence-pattern | Accessibility signals for changed states need current evidence | No changed state accessibility claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [state evidence freshness and tool boundary](references/state-evidence-freshness-and-tool-boundary.md) | evidence-pattern | State evidence freshness, tool boundary, or proof limit remains open | Current source and validation already bind the state evidence and tool boundary | analysis-agent, task-agent, review-agent | evidence-record, validation-plan, proof-limit, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | UI states span loading, denial, partial success, rollback, or recovery | No loading, denial, rollback, or recovery state changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
