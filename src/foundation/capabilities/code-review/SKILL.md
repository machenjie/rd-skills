---
name: code-review
description: "`analysis-agent`/`task-agent`/`review-agent`: use when code needs correctness, security, performance, maintainability, or hallucinated-API review; skip when no review is needed."
---

# code-review

## Registry Trigger

**Use when**

- review code for defects regressions contracts security performance maintainability readability structure quality side effect pollution weak signatures change locality cleanup debt

**Do not use when**

- no task-local code review decision is required

## Skill Role

Inspect a bounded code change for correctness, contract preservation, security and reliability effects, test adequacy, maintainability, and actionable findings. Exclude implementation and release authority.

## High-Value Rules

- **Resolve the review surface.** Identify changed behavior, callers, consumers, data and side effects, generated or configured paths, and relevant repository contracts before judging local lines.
- **Trace consequential paths end to end.** Follow input, validation, authority, state mutation, external effect, failure, cleanup, and observable output far enough to test whether the change preserves its claims.
- **Check invariants and boundary behavior.** Inspect missing, invalid, denied, duplicate, concurrent, partial, stale, timeout, cancellation, and rollback outcomes that are reachable for the changed mechanism.
- **Verify APIs and assumptions from source.** Confirm symbols, signatures, versions, defaults, configuration, framework behavior, and generated contracts rather than accepting plausible names or comments.
- **Evaluate proof against the failure mechanism.** Require focused evidence for the changed behavior and consequential negative outcomes; broad green status or coverage alone does not close an unexercised risk.
- **Classify findings by consequence and evidence.** State the failing condition, reachable impact, source location, confidence, and smallest viable correction, then apply severity from the current review and release policy.
- **Separate defects from optional improvement.** Report behavior, safety, contract, or maintainability risks that affect the change; keep style preference and unrelated redesign outside the blocking verdict.

## Anti-Patterns

- Review only edited lines while indirect consumers, configuration, generated code, or side effects carry the real regression.
- Raise speculative findings without a reachable path, violated contract, or falsifiable consequence.
- Accept a large refactor, mock-only proof, retry-to-green result, or suppression as evidence that the named defect is absent.

## Stop Conditions

Escalate when the review surface is unresolved, critical behavior or authority is externally owned, runtime semantics are unavailable, or a consequential path lacks admissible evidence. Also escalate when the change crosses security, privacy, money, destructive data, public compatibility, concurrency, or production reliability boundaries that need specialist review.

## Output Contract

- bounded review with inspected surface, contract and path evidence, actionable findings, consequence-based severity, proof limits, and non-blocking improvements

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Review spans contracts, security, resources, tests, or rollback risks | The final diff changes no material behavior | review-agent, analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Approval depends on fresh diff, validation, and finding traceability | No review verdict or non-finding claim is being issued | review-agent, analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [finding taxonomy](references/finding-taxonomy.md) | targeted | Borderline findings require severity calibration or industry taxonomy | Ordinary findings already have clear impact and severity | review-agent, analysis-agent, task-agent | gate-decision, residual-risk |
