---
name: input-validation
description: "`analysis-agent`/`task-agent`/`review-agent`: use for input authority, parsing, canonicalization, bounds, state checks, writable fields, rejection, or external-response changes."
---

# input-validation

## Registry Trigger

**Use when**

- define input source authority parsing canonicalization structural and resource bounds current-state constraints writable fields rejection and external-response validation

**Do not use when**

- no task-local input boundary accepted representation state constraint writable field rejection or external-response decision changes

## Skill Role

Define input authority, decoding and canonicalization order, structural and resource bounds, current-state constraints, writable fields, rejection semantics, and external-response validation. Exclude business-rule and permission policy.

## High-Value Rules

- **Name source authority before validation.** Distinguish caller data, authenticated context, server-owned state, provider responses, configuration, generated values, and derived fields so untrusted input cannot override authority.
- **Define one accepted representation.** Specify decoding, normalization, Unicode, whitespace, case, path, numeric, date, identifier, and duplicate-field behavior before equality, lookup, signing, or policy checks.
- **Bound parser and downstream work.** Derive size, count, depth, expansion, range, precision, allocation, query, and fan-out limits from current product, capacity, and abuse constraints, including partial-input behavior.
- **Separate structure from business and state constraints.** Validate shape at the boundary, then apply authoritative eligibility, lifecycle, uniqueness, ownership, and cross-record rules where current state is available.
- **Allowlist writable fields and transitions.** Map accepted input only to owner-authorized commands, fields, identities, and state changes.
- **Make rejection stable and non-leaking.** Preserve machine meaning, field association, safe detail, retryability, and compatibility without exposing secrets, object existence, internal topology, or parser internals.
- **Validate external responses before trust.** Check schema, identity binding, freshness, signatures where applicable, limits, unknown values, and failure behavior before persisting or acting on provider data.

## Anti-Patterns

- Validate before canonicalization, then compare or authorize a differently decoded representation.
- Use schema success as proof of business validity, ownership, safe resource use, or external-response authenticity.
- Bind request objects directly to persistence or domain state, allowing omitted or unexpected fields to mutate authority-owned values.

## Stop Conditions

Escalate when input or state authority is ambiguous, canonical forms can collide, or resource bounds cannot contain untrusted work. Also escalate when writable fields cross permission or invariant boundaries, rejection leaks sensitive state, or external data authenticity and freshness cannot be established.

## Output Contract

- input-validation decision with source authority, canonical representation, structural and resource bounds, state constraints, writable fields, rejection semantics, external-response checks, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | competing authority representation bounds current-state writable-field rejection compatibility or external-response patterns remain viable | one bounded input decision is already complete from the root contract | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | several input boundaries representations constraint classes state checks writable fields rejection outcomes or consumer effects must close together | one bounded field or boundary is already complete from the root contract | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | authority representation canonicalization bounds state replay write-surface rejection compatibility or external-response claims need fresh proof | no task-local validation claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
