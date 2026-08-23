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

Define owned error translation/outcome and diagnostic event/correlation/redaction/volume/reconstruction; consume but do not own protected audit contracts.

## High-Value Rules

- Translate once at the owned boundary while preserving cause, caller action, outcome, and reconstruction correlation.
- Choose no new log until its audience, decision, owner, and outcome are named.
- Load only the Reference for unresolved sensitive content, volume/cardinality, or audit ownership.

## Anti-Patterns

- Local success substituted for evidence of the logging error handling contract.

## Stop Conditions

- Escalate ambiguous ownership, broken correlation, unclear sensitive-data policy, possible secret/tenant leak, unbounded volume, or unreconstructable outcome.

## Output Contract

- logging and error decision with ownership, external meaning, diagnostic events, correlation, outcome classification, redaction, volume bounds, reconstruction evidence, unverified paths or sinks, proof limits, and residual risk
- accepted audit-contract dependency or named `logging-design-gate`/`security-privacy-gate` handoff for each security-relevant outcome; do not claim protected audit-record closure from diagnostic-log evidence

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | log schema correlation redaction or error mapping choices remain unresolved | existing logging policy selects fields levels and client contract | task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects error taxonomy correlation redaction audit or retry context | no logging sink or client-error behavior changes | task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | redaction correlation audit or error-mapping claims need fresh proof | current fixtures and captured outputs prove each logging claim | task-agent, review-agent | evidence-record, proof-limit, residual-risk |
