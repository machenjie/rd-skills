# Engineering Brief

For Analyzed Work, the current Engineering Brief is the only operational
analysis authority. Its authoritative sections are Problem and Desired
Behavior; Acceptance and Non-goals; Ownership and Invariants;

Placement and Reuse; Contract / Data / Failure Impact; Validation Strategy; Risks and
Rollback; First Executable Slice; Task Dependencies; Integration Boundary;
Review Boundary; and Evidence Gaps and Proof Limits.

User requests, change sources, source and tests, external evidence, and
Specialist results are analysis input only. Write source-proven placement
directly into the Brief. Use a corresponding Specialist for a real structural
choice, then incorporate its result into the current Brief before it can affect
implementation. A Specialist never becomes a parallel authority.

Task DAGs, Task Contracts, Implementation Handoffs, and Review Handoffs are
derived artifacts and must not redefine Acceptance, Non-goals, Owner,
Invariants, Placement, contract semantics, Rollback, or the First Executable
Slice. The First Executable Slice is a complete Task Contract v2, not an
informal checklist. Main dispatches it verbatim and never regenerates or
reinterprets it; the DAG planner never reselects it.

Return the First Executable Slice when current evidence proves it safe,
verifiable, reversible, and independent of remaining unknowns. If the Brief is
insufficient, a downstream artifact conflicts with it, or a protected decision
must change, mark the task blocked and return through Main to analysis for an
updated Brief and redispatch of affected tasks.

The public Execution Level lines use Core public `execution-level/v1`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy without v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Engineering Brief

## Status

in_progress / blocked / partial / completed

## Problem and Desired Behavior

## Acceptance and Non-goals

## Ownership and Invariants

## Placement and Reuse

## Contract / Data / Failure Impact

## Validation Strategy

## Risks and Rollback

# Task Plan

## First Executable Slice

Task ID:
Status: in_progress
<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: engineering-brief-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: engineering-brief-template.md -->
Goal:
Owner:
Inputs:
Allowed Read Scope:
Allowed Write Scope:
Non-goals:
Dependencies:
Expected Output:
Acceptance:
Verification:
Evidence Requirements:
Parallel Safety:
Workspace Requirement:
Integration Owner:
Review Owner:
Stop Conditions:
Professional Skill:
Layer 3 Skills:

## Remaining Independent Analysis Scope

State `none` unless the scope is uninspected, non-overlapping, and cannot
invalidate the First Executable Slice.

## Task Dependencies

## Parallel-safe Tasks

## Integration Boundary

Integration Owner:

## Review Boundary

Review Strategy:
Review Owner:
Primary Review Skill:
Covered Task IDs:
Changed Scope:
Specialized Secondary Reviews:

## Evidence Gaps and Proof Limits

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use `current`, `superseded`, or `invalid`. If no source-backed evidence exists,
write `none`, state the proof limit, and do not mark an evidence-dependent result
`completed`.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.
```

Omit the Task Plan only when the requested result is diagnosis-only or
answer-only and no implementation task exists. Do not create ceremonial phase
documents.
