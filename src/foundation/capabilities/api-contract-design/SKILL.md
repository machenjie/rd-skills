---
name: api-contract-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when endpoints, payloads, errors, auth, pagination, idempotency, or compatibility need a contract; skip when APIs are unchanged."
---

# api-contract-design

## Registry Trigger

**Use when**

- design API endpoints resources methods payloads pagination and compatibility

**Do not use when**

- no task-local api contract design decision is required

## Skill Role

Own resource semantics, trusted context, failures, replay, pagination, and compatibility.

## High-Value Rules

- Define operation, resource, consumer, trusted identity, and writable fields.
- Define request, response, error, repeat-delivery, pagination, and completion meaning.
- Select one named Reference for protocol choice, closure, or evidence.
- If the API decision remains active, load only its named Reference.

## Anti-Patterns

- Local success substituted for consumer-contract evidence.

## Stop Conditions

Stop on unknown ownership, identity, replay, pagination, completion, compatibility, or specialist authority.

## Output Contract

- API contract decision with consumer and resource semantics, trusted context, request and response meaning, errors, repeat delivery, pagination or completion, compatibility evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [api style and semantics](references/api-style-and-semantics.md) | targeted | Protocol semantics, versioning, or idempotency choices remain contested | An additive bounded contract change preserves established semantics | analysis-agent, task-agent, review-agent | selected-approach, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | The contract changes pagination, errors, authorization, or replay behavior | Only documentation wording changes; wire behavior remains identical | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Consumer compatibility depends on fresh specs, clients, or contract tests | No consumer-visible contract claim requires validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
