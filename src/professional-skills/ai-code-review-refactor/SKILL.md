---
name: ai-code-review-refactor
description: "Use `review-agent` on implementation or repair diffs for hallucinated APIs, unsupported assumptions, unsafe abstractions, and dependency or regression risks. Skip work without a diff or after reviewer edits."
---

# ai-code-review-refactor

## Role

Support `review-agent` in finding reachable defects in AI-generated or
AI-assisted code through API, architecture, dependency, and behavior evidence.

## When To Use

- implementation diff ready
- repair diff ready for re-review

## Do Not Use

- no actual diff
- reviewer implemented changed scope

## Required Inputs

- acceptance
- boundary summary
- actual diff
- validation evidence

## Professional Decision Rules

- Review specification compliance and code quality against the actual diff and every changed file.
- Prioritize correctness, security, data loss, compatibility, concurrency, failure handling, and regression risk over style.
- Report only reachable findings with severity, path, failure scenario, and correction.

## High-Value Gotchas

- Self-review is not independent evidence.
- Reviewing only the summary misses unmentioned changed files.
- Style findings must not bury a reachable correctness defect.

## Execution Checklist

1. Compare the actual diff and every changed path with acceptance and preserved behavior.
2. Verify referenced APIs, dependencies, ownership, invariants, and changed-code test coverage.
3. Classify only reachable defects with a concrete failure scenario and source evidence.
4. Stop approval when the diff, a changed path, or evidence freshness cannot be established.

## Stop / Escalation Conditions

- Escalate authentication, authorization, permissions, payments, sensitive
  data, secrets, or credentials to `security-privacy-gate`.
- Escalate unsafe logs, raw prompts, tokens, PII, or full command-output artifacts
  to `security-privacy-gate`.
- Escalate to `data-api-contract-changer` when a refactor silently alters API response shapes, error codes, or contract semantics.
- Escalate to `architecture-impact-reviewer` when AI introduces a new service boundary, shared abstraction, or cross-module dependency.
- Escalate to `data-middleware-change-builder` when a generated migration script, ORM query, or schema change is involved.
- Escalate when AI has added or upgraded a dependency with known CVEs, GPL/AGPL license conflict, or broad transitive attack surface.
- Escalate when the refactor is large enough that behavioral equivalence cannot be established without running the full integration test suite.
- Keep missing or stale evidence required for the current diff, scope, or closure
  as a blocking finding; name the unavailable evidence and unblock condition.
- For repeated same-path failure, follow the Core `retry_policy`: return control
  to the main agent or report the review blocked.
- Route a known failure mechanism with material same-pattern regression exposure
  to `regression-testing`; otherwise keep recurrence scope and exclusions in the
  review finding.
- Escalate to `code-element-professionalism` for generated local defaults, shadowing, hidden expression side effects, no-op statements, cleanup gaps, fallthrough, or event-before-commit ordering.

## Output Contract

- reviewed files
- unreviewed files with reason and residual risk
- reachable findings with severity, path, failure scenario, evidence, and correction
- verified API, dependency, invariant, placement, and behavior decisions
- changed-code test evidence and unverified AI-specific risk
- explicit no-finding result when no reachable defect remains

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [ai review pattern catalog](references/ai-review-pattern-catalog.md) | benchmark-pattern | Findings need pattern-calibrated examples for recurring AI failure modes | The issue is already concrete and no calibration examples are needed | review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | A bounded review needs a compact checklist before approval | Pattern examples or exhaustive gates are required | review-agent | checklist-result, residual-risk |
| [index](references/index.md) | index | competing ai code review refactor references require dependency, conflict, or output-fragment selection | the ai code review refactor root or a task-named reference already resolves selection | review-agent | reference-selection |
| [review output and gates](references/review-output-and-gates.md) | targeted | L5 review needs exhaustive schema, quality gates, handoff routing, or repair/re-review semantics | A compact severity finding list is sufficient | review-agent | gate-decision, residual-risk |
| [solution optimality](references/solution-optimality.md) | targeted | An AI-generated diff introduces a material algorithm, data-structure, concurrency, cache, abstraction, or measurable resource-use choice | The issue is already a concrete finding or no material implementation choice changed | review-agent | selected-approach, residual-risk |
