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

The Analysis assignment and Engineering Brief itself have no Execution Level,
apply no default L3, write no historical effective level, and do not
participate in historical maxima. Compute the executable Task Level only after
this Brief has identified the First Executable Slice, using the analysis
handoff as evidence. The Level fields below belong only to that executable
Slice.

Return the First Executable Slice when current evidence proves it safe,
verifiable, reversible, and independent of remaining unknowns. If the Brief is
insufficient, a downstream artifact conflicts with it, or a protected decision
must change, mark the task blocked and return through Main to analysis for an
updated Brief and redispatch of affected tasks.

Complete one initial Analysis by closing observable Acceptance,
Owner/Placement/Invariant, Acceptance-proving Validation, executable task
dependencies, professional Skill boundaries, minimum sufficient Review
Boundaries, and critical gaps blocking the First Executable Slice. Task
completion or switch, ordinary implementation discovery, and an unreached
Review Boundary do not re-trigger Analysis.

The first Analysis event is always `initial`. Desired behavior and observable
Acceptance are target authority; observed behavior is failure evidence only and
cannot be copied into Acceptance. A Delta is legal only after this complete
initial Brief is accepted and current evidence names the protected decision it
invalidates. Before dispatch, close every authoritative Brief section and every
non-blocked First Executable Slice field, then preserve the Slice's Professional
Skill and Layer 3 selections verbatim.

When this Brief must select Layer 3 for an analyzed downstream Task or Review,
use the Host-selected Professional root and its already-loaded entrypoint line:

JIT: `references/runtime/selector.json`; Runtime: `<V>/<B>`.

Validate frontmatter Professional plus `V/B` against the logical selection
receipt's `build` and every current selector, partition, or Layer 3 marker on
its existing read. Never read an identity sidecar, reread a selector for this
check, read root/integrity manifests, calculate digests, or search HOME,
parents, siblings, or globs. Missing, malformed, stale, or mismatched bindings
fail closed without Utility or reroute. If the exact set is fixed, skip
selector/shards and validate only the entrypoint, receipt, fixed-path exact
Layer 3, and named References.
Write the exact set into the Brief; downstream Task and Review do not reroute.
Main still owns Direct and initial-Analysis selection.

Analysis remains read/search-only. Only when a material Claim cannot close from
current read/search evidence and one bounded executable observation can decide
it, return one Evidence Request keyed by Analysis Task ID, Continuation ID, and
Claim ID. The contract is one logical request, at most two Host attempts after
one denied-before-observation exact-authority retry, and one observation. Main
dispatches no-Skill/no-Layer-3/no-edit Utility and returns evidence, freshness,
scope, and Proof Limit to the same initial or Delta Analysis. Unsupported or
refused evidence becomes a Proof Limit; permission never changes the route.

Delta Analysis is permitted only when evidence invalidates Acceptance/Non-goals,
Owner/Placement/Invariant, contract/data semantics, dependency/rollback,
material risk, or a scope blocker. Reuse Core `delta_analysis`; do not change
its invalidation triggers or transitive scope. After Delta Analysis, the
complete updated Engineering Brief remains the only operational analysis authority.
Then emit only this decision projection:

```text
Delta Impact:
invalidated=[...];
affected={
  brief:[...],
  tasks:[...],
  dependencies:[...],
  skills:[...],
  reviews:[...]
};
unlisted=preserved
```

Each list is the exact proved affected set; `[]` means proved no impact, while
unknown requires a Proof Limit rather than `[]`. Preserve Skill assignments unless professional domain, work type, or
a material-risk trigger changes. If transitive impact is not closed, record a
Proof Limit and return blocked. Main consumes Delta Impact without reinterpreting affected scope.
Use full re-analysis only when foundational goals or system assumptions are
invalidated. Delta Impact never replaces, summarizes, or weakens the Brief.

The public Execution Level lines use Core public `execution-level/v2`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Engineering Brief

## Status

in_progress / blocked / partial / completed

## Problem and Desired Behavior

## Acceptance and Non-goals

## Ownership and Invariants

Exact path/symbol/owner = direct-read-first selector, not owner proof. Stop on
current-source confirmation; bounded-correct only within the same
owner/route/contract; protected contradiction = Main/Delta. Repository facts
never rewrite Desired Behavior, Acceptance, Non-goals, or target architecture.

## Placement and Reuse

## Contract / Data / Failure Impact

## Validation Strategy

## Risks and Rollback

# Task Plan

## First Executable Slice

Task ID:
Status: in_progress
<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: engineering-brief-template.md -->
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
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

Review Owner:
Review Boundary ID:
Review Strategy: combined-final / risk-triggered-intermediate:<Core trigger> / L5-preimplementation / L5-final
Review Round ID:
Effective Level:
Required Review Skills:
Specialist Obligations:
Covered Task IDs:
Required Changed Scope:
Professional Risk Dimensions:
Required Validation / Evidence Binding:
Review Assignments: one primary and zero or more specialists; each has Assignment ID, role, review-agent profile, exactly one Review Skill, zero to three review-risk-routed Layer 3 Skills, selection basis, and bounded scope
Primary Close Ordering: every required specialist result is current before the primary emits the sole combined artifact

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
