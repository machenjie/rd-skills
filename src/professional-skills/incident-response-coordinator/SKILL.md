---
name: incident-response-coordinator
description: "Use `analysis-agent` for active multi-responder incident command, cadence, mitigation, communications, or handoff. Skip ordinary diagnosis, reliability design, release approval, post-incident docs, and execution."
---

# Incident Response Coordinator

## Role

Use `analysis-agent` to coordinate evidence, options, workstreams, and the shared record. It may analyze, but may not operate, approve production actions, or infer authority from urgency.

## When To Use

- Multiple responders or workstreams need one command structure.
- Impact needs a shared severity and update cadence.
- Diagnosis, mitigation, communications, and handoff need synchronization.

## Do Not Use

- Route ordinary diagnosis to `engineering-change-analysis` and its failure-diagnosis path.
- Route reliability design or review to `reliability-observability-gate`.
- Route a release or rollback decision to `delivery-release-gate`.
- Route post-incident documentation to `change-documentation-gate`.
- Do not use this Skill to mutate production, deploy, execute a destructive action, or bypass operator authority.

## Required Inputs

- Trigger, observed impact, scope, and known onset.
- Responders, operational authority, constraints, and communication channels.
- Evidence, active changes, mitigation proposals, and update cadence.

## Professional Decision Rules

1. Assign an incident identifier and record scope, impact, onset, status, and policy-based severity. Mark uncertain values provisional.
2. Name the commander, technical lead, mitigation operator, communications lead, scribe, and authority owner. One person may hold several roles only when every responsibility remains explicit.
3. Keep timestamped evidence, freshness, hypotheses, actions, decisions, outcomes, and checkpoints in the shared incident log.
4. Give each concurrent workstream one owner, action scope, dependency set, authority boundary, and reporting cadence.
5. Keep technical diagnosis and signal interpretation with their existing capability owners.
6. Keep mitigation proposed until a named authorized operator accepts it. Record impact, blast radius, reversibility, stop conditions, validation, and unknown outcomes.
7. Publish communications from one verified source of truth. Separate confirmed facts, uncertainty, user impact, sensitive detail, and the next update time.
8. Close only after recovery is verified, active changes are reconciled, temporary controls have owners, and the closure or handoff record is complete.

## High-Value Gotchas

- Role ambiguity leaves decisions or actions without an accountable owner.
- Parallel unlogged changes corrupt diagnosis and recovery evidence.
- A stale timeline makes obsolete facts appear current.
- Unsafe mitigation is mistaken for authorized execution.
- Communications divergence creates conflicting internal and external status.
- Premature closure hides unresolved impact or temporary controls.
- Handoff loss drops authority, context, actions, or verification obligations.

## Execution Checklist

1. Bound the incident and establish command, severity, authority, roles, and cadence.
2. Open the shared record and divide active work into owned workstreams.
3. Coordinate evidence, hypotheses, and mitigation proposals without operating the system.
4. Synchronize decisions, communications, recovery signals, and unresolved risk.
5. End coordination with explicit closure evidence or a live commander handoff.

## Companion Boundary

- Load `failure-diagnosis` for causal investigation and recurrence proof.
- Load `observability` for signal selection, freshness, and interpretation.
- Load `release-rollback` only when a mitigation option needs rollback mechanics; the approval decision remains with `delivery-release-gate`.

## Stop / Escalation Conditions

- Stop when no commander, authority owner, or action owner can be named.
- Stop when a proposed action is destructive, irreversible, or unsafe without an authorized operator and a recovery path.
- Return bounded workstream ownership when execution spans multiple tasks; `analysis-agent` does not dispatch or perform those tasks.
- Escalate any live mutation, deployment, release, rollback approval, or privileged action to the responsible operator and governing workflow.

## Output Contract

Return an `Incident Coordination Record` containing:

- scope, severity, status, roles, authority, and cadence;
- timestamped evidence, decisions, actions, outcomes, and communications;
- workstream owners, dependencies, permissions, and checkpoints;
- mitigation authority, recovery, stop, and verification requirements;
- closure or handoff state, residual risks, and proof limits.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [command cadence and decision log](references/command-cadence-and-decision-log.md) | targeted | Establishing command, cadence, workstreams, or the shared incident record | One owner is performing ordinary diagnosis or the incident is already closed | analysis-agent | decision-record, proof-limit, residual-risk |
| [mitigation authorization and handoff](references/mitigation-authorization-and-handoff.md) | targeted | Coordinating mitigation, recovery verification, closure, or transfer of command | The task is only diagnosis release approval reliability design or post-incident documentation | analysis-agent | failure-decision, decision-record, residual-risk |
