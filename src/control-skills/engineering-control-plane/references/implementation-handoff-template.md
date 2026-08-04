# Implementation Handoff

Return this visible contract after the last material edit and its targeted
validation. It records evidence, not implementer reasoning or self-review.

The public Execution Level lines use Core public `execution-level/v1`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy without v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Implementation Handoff

## Status

in_progress / blocked / partial / completed

## Task ID

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: implementation-handoff-template.md -->
Level: requested=unspecified / L1 / L5; automatic=L2 / L3 / L4; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: implementation-handoff-template.md -->

## Owner

## Result

## Expected Output

## Evidence Requirements

## Changed Files

## Actual Diff or Host-native Diff Reference

Provide the actual diff or an accessible host-native reference. A changed-file
summary is not a diff. Write `not applicable — no material edits` only when no
material edit occurred.

## Commands Run

## Validation Results

## Last Material Edit and Validation Ordering

Name the last material edit and the validation run after it. Any material edit
invalidates older validation and review evidence.

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

State is `current`, `superseded`, or `invalid`. Repair supersedes
evidence for the previous diff and requires fresh validation and re-review.
Current task-agent evidence after the latest material edit uses
`latest-material-edit` and `validation-passed` Claim values.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.

## Unverified Scope

## Residual Risk
```

Keep the Evidence Ledger task-local, handoff-visible, and non-persistent. Use
no daemon, database, private evidence storage, runtime task state engine, or
hidden protocol record. Include no private prompts, secrets, full logs, hidden
state, or substitute approval verdict.
