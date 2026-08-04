# Review Handoff

The review-agent receives one bounded target and does not edit. Implementation
review requires observable acceptance, the latest actual diff, the declared
changed-path set, current validation results, and the Evidence Requirements.

The public Execution Level lines use Core public `execution-level/v1`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy without v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Review Handoff

## Status

in_progress / blocked / partial / completed

## Task ID

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: review-handoff-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: review-handoff-template.md -->

## Owner

## Result

Verdict: pass / findings / blocked

## Expected Output

## Evidence Requirements

## Reviewed Target

Type: implementation diff / pre-implementation artifact
Name or scope:

## Changed Files

Required for implementation or repair review. Write `not applicable` for a
pre-implementation artifact.

## Artifact and Supporting Evidence

Required for pre-implementation artifact review. Write `not applicable` for
an implementation diff review.

## Commands Run

## Validation Results

## Findings

For each finding, state severity, description, affected path, and acceptance
or risk impact. Do not invent private identifiers.

## Core Review Discipline

At L1-L5, decide every base dimension from independent evidence: actual latest
diff, every changed file, observable acceptance, validation freshness,
regression mechanism, negative and boundary behavior, ownership and placement,
unnecessary scope, unverified scope, and residual risk. A Level may add depth,
independence, or evidence, but cannot remove a base dimension. For non-code or
other implementation work without an actual diff, block approval and mark the
affected dimensions unverified; never fabricate a diff.

**Professional Risk Matrix**

<!-- BEGIN CHANGEFORGE CORE PROFESSIONAL RISK MATRIX -->
For every assigned Review Skill at L1-L5, record exactly one decision per
Core professional-risk dimension. Allowed statuses: `verified`, `finding`, `not-applicable`, `delegated`, `blocked`.
`not-applicable` requires a source-backed reason and evidence. `delegated`
requires a named registered Review Skill, scope, and reason. A missing,
duplicate, or unknown dimension or status blocks the verdict.

| Dimension | Status | Reason | Evidence | Specialist Skill | Delegated Scope |
| --- | --- | --- | --- | --- | --- |
| `correctness-invariants` |  |  |  |  |  |
| `authority-security-privacy` |  |  |  |  |  |
| `failure-recovery-concurrency` |  |  |  |  |  |
| `performance-resources` |  |  |  |  |  |
| `contracts-data-consumers` |  |  |  |  |  |
| `tests-evidence` |  |  |  |  |  |
| `maintainability-structure` |  |  |  |  |  |
| `operations-documentation-release` |  |  |  |  |  |
<!-- END CHANGEFORGE CORE PROFESSIONAL RISK MATRIX -->

After repair, require fresh validation, then the latest actual diff, then fresh
re-review. An older review cannot cover the new modification.

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use only `current` evidence. Mark evidence from an older diff `superseded` or
`invalid`. A material edit invalidates older evidence. Repair requires fresh validation
and re-review of the latest diff.
Current review-agent evidence after the latest material edit uses
`changed-scope-reviewed`, `high-risk-review-passed` when applicable, and
`blocking-findings-none` or `blocking-findings-resolved` Claim values.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.

## Reviewed Scope

## Unreviewed Scope

## Unverified Scope

## Residual Risk

## Recommended Next Step
```

The Evidence Ledger is a visible, task-local handoff section. It is not private
storage, a runtime database, or a task state engine.
