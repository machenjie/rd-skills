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

Inspect a bounded latest diff for consequential correctness, contract, security,
reliability, evidence, and maintainability defects. Exclude mutation, rerouting,
and release authority.

## High-Value Rules

- Resolve the Current Task Boundary, latest diff, changed files, and reachable consumers before judging lines.
- Trace consequential input, authority, mutation, effect, failure, cleanup, and output paths.
- Verify source APIs and assumptions.
- Match evidence to the failure mechanism and classify `current-task`, `scope-blocker`, or `adjacent` before severity.
- Preserve Brief authority and separate actionable defects from optional improvement.

## Anti-Patterns

- Local success substituted for evidence of the code review contract.

## Stop Conditions

Stop on an unresolved review surface, external authority, unavailable semantics, or missing consequential-path evidence; invoke the relevant specialist for security, privacy, money, destructive data, compatibility, concurrency, or production risk.

## Output Contract

- bounded review with inspected surface, contract and path evidence, actionable findings, consequence-based severity, proof limits, and non-blocking improvements

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [checklist](references/checklist.md) | decision-checklist | Review spans contracts, security, resources, tests, or rollback risks | The final diff changes no material behavior | review-agent, analysis-agent, task-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Approval depends on fresh diff, validation, and finding traceability | No review verdict or non-finding claim is being issued | review-agent, analysis-agent, task-agent | evidence-record, proof-limit, residual-risk |
| [finding taxonomy](references/finding-taxonomy.md) | targeted | Borderline findings require severity calibration or industry taxonomy | Ordinary findings already have clear impact and severity | review-agent, analysis-agent, task-agent | gate-decision, residual-risk |
