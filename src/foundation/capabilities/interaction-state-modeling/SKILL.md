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

Define user-visible interaction states, transition triggers, authoritative outcomes, uncertainty, available actions, recovery, accessibility signaling, and evidence. Exclude backend lifecycle and authorization policy.

## High-Value Rules

- **Derive states from product and operation semantics.** Name observable distinctions that change message, action, risk, or recovery rather than imposing a fixed generic state list.
- **Keep empty, denied, missing, failed, pending, and complete distinct.** Map each state to current authority, disclosure limits, user meaning, and allowed next action so one condition cannot masquerade as another.
- **Preserve unknown outcomes.** A timeout, disconnect, cancellation request, or lost response does not prove the authoritative operation stopped; offer reconciliation or safe retry according to the side-effect contract.
- **Coordinate optimistic state with authoritative state.** Define provisional ownership, server rejection, conflicting updates, rollback or reconciliation, duplicate action prevention, and the message shown when local and durable outcomes diverge.
- **Make unavailable actions understandable and operable.** Distinguish permission, prerequisite, in-progress, unavailable dependency, policy, and unsupported state, then preserve focus, explanation, and an accessible recovery path where one exists.
- **Model asynchronous and partial completion.** Represent accepted, queued, processing, partially applied, completed, failed, and compensated outcomes only where the backend contract exposes them, including refresh and stale-view behavior.
- **Prove transitions and forbidden states.** Exercise task-relevant success, denial, empty, retry, timeout, stale response, navigation, refresh, and assistive-technology signals against current frontend and service evidence.

## Anti-Patterns

- Show success from request acceptance, optimistic mutation, or local completion before the authoritative effect is known.
- Collapse permission denial, absence, filtering, and load failure into a single empty or error treatment that leaks or misstates state.
- Disable an action without an owned reason or recovery path, or let a late response overwrite newer user intent.

## Stop Conditions

Escalate when authoritative outcome or disclosure policy is unknown, repeat action can duplicate consequential effects, optimistic recovery can lose data, or asynchronous work lacks a completion source. Also escalate when late responses cannot be ordered or accessible state and recovery cannot be verified.

## Output Contract

- interaction-state decision with authoritative state mapping, transitions, uncertainty, available actions, optimistic and asynchronous behavior, accessibility signals, forbidden states, evidence limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | State machine, accessibility, background-refresh, or timeout semantics need calibration | No interactive state or transition changes | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | UI states span loading, denial, partial success, rollback, or recovery | No loading, denial, rollback, or recovery state changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | State claims require fresh backend, story, ARIA, and transition proof | No state-completeness or accessibility claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
