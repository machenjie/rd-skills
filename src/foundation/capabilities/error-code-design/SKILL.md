---
name: error-code-design
description: "`task-agent`: use when error codes, safe messages, retryability, remediation, status mapping, or client behavior needs a stable contract; skip when no error contract changes."
---

# error-code-design

## Registry Trigger

**Use when**

- design error model codes messages remediation and client behavior

**Do not use when**

- no task-local error code design decision is required

## Skill Role

Define stable external error identity, classification, safe detail, retry and remediation meaning, boundary mapping, compatibility, and consumer evidence. Exclude logging, transport design, and domain rules.

## High-Value Rules

- **Give each code one stable decision meaning.** Bind it to a caller-relevant condition, scope, authoritative source, and expected handling rather than an implementation exception or free-text message.
- **Separate classification dimensions.** Model validation, absence, conflict, permission, dependency, transient, permanent, unknown, and partial outcomes plus retryability, user action, and support action independently where consumers need them.
- **Keep messages safe and adaptable.** Preserve machine identity outside localized text, expose only detail needed for correction or correlation, and avoid secrets, object existence, internal identifiers, stack data, and topology.
- **Map at the owning boundary.** Translate internal causes to domain or external meaning once the necessary context is available, then apply transport semantics from the current protocol contract without leaking implementation categories.
- **Handle aggregate and field errors deterministically.** Define ordering, duplicates, paths, nested causes, partial success, and truncation so clients can render and act without parsing prose.
- **Preserve compatibility and unknown handling.** Treat code removal, reuse, changed retry meaning, changed field association, and newly introduced values as consumer contract changes with a mixed-version path.
- **Prove consumer behavior.** Exercise representative clients against validation, denial, conflict, retryable, permanent, unknown, partial, and unexpected conditions, including safe fallback for unrecognized codes.

## Anti-Patterns

- Reuse one generic code for unrelated conditions or encode changing implementation names in public identity.
- Make clients parse localized messages, stack fragments, or transport text to decide retry and remediation.
- Mark failures retryable without operation idempotency, aggregate retry budget, and authoritative outcome semantics.

## Stop Conditions

Escalate when condition authority is ambiguous, error detail can leak protected state, retry can duplicate consequential effects, or consumers depend on unstable text. Also escalate when transport and domain meanings conflict, or unknown-code fallback cannot remain safe.

## Output Contract

- error contract decision with stable identity, classification, safe detail, retry and remediation meaning, boundary mapping, compatibility, consumer evidence, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Errors change codes, statuses, retry behavior, or diagnostic separation | No client-visible failure contract changes | task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Error claims require fresh negative tests and consumer evidence | No compatibility, redaction, or retryability claim needs proof | task-agent | evidence-record, proof-limit, residual-risk |
| [industry benchmarks](references/industry-benchmarks.md) | benchmark-pattern | Public error semantics, retryability, or disclosure rules need calibration | The private error never crosses a client boundary | task-agent | option-comparison, selected-approach |
