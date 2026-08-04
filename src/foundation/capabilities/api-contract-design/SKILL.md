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

Define resource and operation semantics, requests, responses, identity context, errors, repeat delivery, pagination, compatibility, and consumer proof. Exclude controller implementation, permission policy, and domain invariants.

## High-Value Rules

- **Start from consumer goal and resource semantics.** Name operation meaning, authoritative resource, affected consumers, state and side effects, consistency, and current contract source before choosing route or payload shape.
- **Separate caller data from trusted context.** Define subject and tenant provenance, object identity, writable fields, permission handoff, and server-owned values without treating authentication as action authorization.
- **Specify request and response meaning completely.** Cover required, optional, absent, null, default, unknown, partial, pagination, ordering, content, and compatibility behavior that consumers can observe.
- **Make failure externally stable and safe.** Define machine meaning, retryability, field association, conflict or unknown outcome, safe detail, and transport mapping according to the current protocol contract.
- **Coordinate repeat delivery with side effects.** Define operation identity, duplicate and concurrent request behavior, timeout, cancellation, result reuse, and reconciliation from the authoritative business effect.
- **Design pagination and long-running outcomes honestly.** Preserve stable ordering and continuation identity, distinguish acceptance from completion, and expose progress or terminal status only where the underlying operation supports it.
- **Prove mixed-consumer compatibility.** Exercise representative current clients, old and new request or response combinations, errors, unknown values, rollback, generated artifacts, and unverified external consumers.

## Anti-Patterns

- Mirror database or internal domain objects directly into an external contract.
- Return transport success with a hidden business failure, or expose raw exceptions and internal identifiers.
- Label an additive schema change safe while defaults, strict validation, exhaustive matching, ordering, or side effects change.

## Stop Conditions

Escalate when consumer or resource ownership is unknown, permission or identity boundaries are ambiguous, repeat delivery can duplicate consequential effects, or pagination or completion semantics are unstable. Also escalate when compatibility populations are uninspected or public, partner, financial, regulated, or destructive behavior lacks specialist ownership.

## Output Contract

- API contract decision with consumer and resource semantics, trusted context, request and response meaning, errors, repeat delivery, pagination or completion, compatibility evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [api style and semantics](references/api-style-and-semantics.md) | targeted | Protocol semantics, versioning, or idempotency choices remain contested | An additive bounded contract change preserves established semantics | analysis-agent, task-agent, review-agent | selected-approach, residual-risk |
| [checklist](references/checklist.md) | decision-checklist | The contract changes pagination, errors, authorization, or replay behavior | Only documentation wording changes; wire behavior remains identical | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Consumer compatibility depends on fresh specs, clients, or contract tests | No consumer-visible contract claim requires validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
