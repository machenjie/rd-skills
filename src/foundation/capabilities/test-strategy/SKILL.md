---
name: test-strategy
description: "`analysis-agent`/`task-agent`/`review-agent`: use to recommend a risk-to-test evidence portfolio and omissions; skip test implementation, fixed-command, and release-verdict work."
---

# test-strategy

## Registry Trigger

**Use when**

- choose risk based proof portfolio test levels failure mechanisms oracles omissions and admissibility evidence

**Do not use when**

- one test level and command are already fixed or the task only implements tests or decides release readiness

## Skill Role

Recommend the smallest task-specific proof portfolio by mapping risks and failure mechanisms to observable oracles, test levels, command-signal requirements, omissions, and evidence limits. Exclude exact command selection, detailed case design, validation judgments, and release verdicts.

## High-Value Rules

- **Map the failure before choosing a level.** Each selected test names the defect mechanism, consequence, affected surface, and observable oracle; habit, framework availability, and coverage targets are insufficient selectors.
- **Smallest task-specific portfolio.** Map the triggered mechanism to the cheapest test level that can exercise it.
- **Test-level escalation excludes risk-label-only layering.** Recommend another level only when it observes a distinct material mechanism, boundary, consumer, or oracle.
- **Validation boundary.** Describe mechanism-sensitive assertions and command signals for `quality-test-gate`, leaving exact entrypoints, affected-test/dependent coverage, and fallback selection to `targeted-validation-selection`.
- **Model negative and nondeterministic outcomes.** Include reachable denial, invalid input, conflict, timeout, rollback, retry, partial failure, and duplicate effects. For concurrency or eventual consistency, assert allowed terminal results and forbidden states with bounded observable waits rather than one scheduler interleaving.
- **Flake containment.** Record retry or quarantine with its first failure, reproduction inputs, logs, owner, remediation condition, and `quality-test-gate` admissibility question.
- **Make omissions reviewable.** Record the technical reason, compensating evidence, residual risk, owner, reopen trigger, and release consequence for each omitted level.
- **Release judgment.** Route release-relevant evidence to `delivery-release-gate` for its go/no-go decision.

## Anti-Patterns

- Reject layer catalogs without a task-specific failure mechanism or oracle.
- Reject coverage percentage or full-suite status presented as behavior proof.
- Reject broad end-to-end substitution for rule matrices, mocks for a real-risk seam, or manual checks without exact steps, expected outcomes, artifacts, and owner.
- Flag stale or partial results, flaky retries, and skipped tests with their containment and proof limits for `quality-test-gate` judgment.

## Stop Conditions

Stop and return the unresolved portfolio when acceptance behavior or failure consequence is unknown, affected consumers or boundaries are uninspectable, or required environments or fixtures are unavailable. Also stop when security, destructive data, regulated, concurrency, capacity, or rollback risk lacks an accountable evidence owner. Repository inspection and local commands prove only inspected paths and environments. They do not prove hidden consumers, production scale, or release readiness.

## Output Contract

- risk based test strategy decision with failure mechanisms oracles proof levels coverage obligations omissions command-signal requirements and admissibility limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Test levels layered proof assertion challenge or omission tradeoffs remain contested | One accepted portfolio covers each material failure mechanism | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Negative paths nondeterminism flaky containment omissions and risk tracing need multi-part closure | The accepted portfolio already closes those decisions | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Admissibility depends on fresh changed-path consumer command fixture or report evidence | No strategy-confidence claim awaits proof | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
