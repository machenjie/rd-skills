# Direct Task Contract v2

Direct Task requires explicit behavior, local scope, owner, observable
acceptance, non-production verification, placement, and rollback; work is
low-risk, reversible, and clear of excluded boundaries or unresolved material
impact. Otherwise route to Analyzed Work.

Direct Task is outside the Analyzed Work authority path. It keeps this
template's existing field authority and does not create or derive authority
from an Engineering Brief.

An unknown owner/module/system/verification boundary routes to Analyzed Work.
Inside an already-known stable owner/test/consumer boundary, bounded
confirmation may inspect only the named checks below. Use `not applicable` for
a field that has no Direct Task value.

The public Execution Level lines use Core public `execution-level/v2`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Direct Task Contract v2

## Task ID

## Status

in_progress

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: direct-task-template.md -->
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: direct-task-template.md -->

## Goal

## Owner

## Inputs

## Allowed Read Scope

## Allowed Write Scope

## Inspection Boundary

Name the already known owner, test, and consumer boundaries. Direct bounded
discovery requires a stable Primary Professional, Domain / Layer3 route,
semantic scope, no unresolved user choice or material risk, and a bounded read
boundary. Known exact file, symbol, or section locations—and any exact owner
claim—are selectors, not owner proof: read them first. When current source confirms its owning/change
role, stop discovery. A same-owner/route/contract rename or move permits only
bounded correction and never changes the Brief; an owner/module/public
contract/security/migration/external-consumer contradiction stops before edit
and returns through Main. Direct has no accepted Brief, so this requests
initial Analysis, never Delta. Otherwise search candidate locations, then read
the minimum complete evidence needed for the decision; widen only when current
source remains insufficient. Search, Top-K, ranked results, repository maps,
truncated results, prior summaries, and nearby files are selectors, not proof.
Top-K is not a complete corpus. Completeness claims require declared coverage
or a Proof Limit. Within the already-known owner boundary, inspection may
confirm only:

- exact owning symbol/file;
- relevant existing test;
- minimum local consumer;
- local reuse candidate;
- local validation command; and
- placement within the already-known owner boundary.

Prohibit repo-wide discovery, an unknown owner/module/system or external
consumer graph, security/money/migration/domain-boundary discovery, Worker
rerouting, and Worker selection of a new Skill, Domain, or Layer3.

## Inspection Stop Conditions

The only outcomes are: confirm and continue; route/risk invalidated -> stop
before editing and return to Main for Analysis; user-owned choice discovered ->
stop before editing and return to Main, which asks one minimum concrete
question. A simpler discovery never lowers the current Level; higher risk
requires Main to recompute it. Task and Review workers never reroute.
Current source proves repository facts only; it cannot rewrite Desired
Behavior, Acceptance, Non-goals, or target architecture.

## Non-goals

## Expected Output

## Acceptance

## Verification

## Evidence Requirements

Name the claims, commands, artifacts, freshness requirement, scope, and proof
limits that must appear in the task-local Evidence Ledger.
Analysis anchors may supply path, symbol/range, claim, scope, freshness, and
Proof Limit selectors. Task still proves material claims from current source;
Review confirms them independently and never inherits correctness or coverage.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.

## Parallel Safety

## Workspace Requirement

## Integration Owner

Write `not applicable` when no integration occurs.

## Review Owner

## Stop Conditions

## Professional Skill

Primary:
Layer 3 (only triggered items):
Review:
```

Do not add private runtime state, a hidden protocol record, or a Task DAG.
