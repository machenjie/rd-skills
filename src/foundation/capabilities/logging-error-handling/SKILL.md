---
name: logging-error-handling
description: "`task-agent`/`review-agent`: use when structured errors, logs, correlation, redaction, propagation, or safe diagnostics change; skip when logging/error handling is unaffected."
---

# logging-error-handling

## Registry Trigger

**Use when**

- design structured errors logging context propagation and safe diagnostics

**Do not use when**

- no task-local logging error handling decision is required

## Skill Role

Define error meaning and propagation, diagnostic purpose, structured context, correlation, redaction, outcome classification, volume bounds, and evidence that failures remain actionable. This Skill may identify a security-relevant outcome and consume an accepted audit contract, but excludes ownership of protected audit-record semantics, integrity, retention, access, durability, and alert policy.

## High-Value Rules

- **Define error ownership and external meaning.** Preserve causal context across layers while translating only at owned boundaries; distinguish user, domain, dependency, transient, permanent, cancellation, and unexpected outcomes relevant to caller action.
- **Log an owned diagnostic event, not arbitrary data.** Name audience, decision enabled, event point, stable identity, outcome, and retention need before selecting fields or severity.
- **Preserve correlation across attempts and effects.** Carry request, operation, trace, job, message, tenant-safe, and real or effective actor identity needed to reconstruct a causal path without confusing retries with distinct business operations.
- **Classify terminal outcome accurately.** Avoid reporting handled intermediate retries, expected denial, cancellation, or fallback as terminal errors, and avoid hiding exhausted or partially applied work behind informational success.
- **Minimize sensitive and unbounded content.** Exclude secrets and raw bodies by default, transform personal or regulated fields according to current policy, and bound message, stack, collection, key, and payload expansion.
- **Control volume and cardinality at the source.** Derive event rate, level, sampling, aggregation, dynamic labels, and hot-path detail from current diagnostic need, cost, and incident consequence.
- **Separate diagnostics from audit records.** Identify the security-relevant outcome, accepted audit dependency, unresolved semantics, integrity, retention, access, sink, or durability, named specialist handoff, and gap without claiming protected-record closure.
- **Prove failure reconstruction and redaction.** Exercise representative normal, denied, retry, timeout, cancellation, partial, and unexpected paths, then verify correlation, terminal classification, sensitive-field handling, and proof limits.

## Anti-Patterns

- Log the same exception at each layer, producing duplicate noise without additional ownership or action.
- Store raw requests, tokens, personal data, stack detail, or dynamic high-cardinality values because they might help later.
- Treat a fallback or retry as success while the original failure, final disposition, or lost effect cannot be reconstructed.

## Stop Conditions

Escalate when error ownership is ambiguous, correlation cannot join consequential effects, sensitive-field policy is unclear, or logging can expose secrets or tenant data. Also escalate when hot-path volume is unbounded, or current evidence cannot reconstruct the terminal outcome.

## Output Contract

- logging and error decision with ownership, external meaning, diagnostic events, correlation, outcome classification, redaction, volume bounds, reconstruction evidence, unverified paths or sinks, proof limits, and residual risk
- accepted audit-contract dependency or named `logging-design-gate`/`security-privacy-gate` handoff for each security-relevant outcome; do not claim protected audit-record closure from diagnostic-log evidence

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | log schema correlation redaction or error mapping choices remain unresolved | existing logging policy selects fields levels and client contract | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects error taxonomy correlation redaction audit or retry context | no logging sink or client-error behavior changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | redaction correlation audit or error-mapping claims need fresh proof | current fixtures and captured outputs prove each logging claim | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
