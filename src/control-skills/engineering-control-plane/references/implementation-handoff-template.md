# Implementation Handoff

Return this visible contract after the last material edit and its targeted
validation. It records evidence, not implementer reasoning or self-review.
The normal sequence is one Task's final edit, fresh validation, exact change
capture, this same Implementation Handoff, and Main's readiness gate. Do not
use a second Task or normal recovery/export Task to complete that sequence.

For Analyzed Work, this handoff is a derived projection of the current
Engineering Brief and its verbatim-dispatched First Executable Slice. Result
and evidence may report execution but must not redefine Acceptance, Non-goals,
Owner, Invariants, Placement, contract semantics, Rollback, or the Slice. If
the assignment conflicts with the current Brief or needs one of those decisions
to change, mark it blocked and return to analysis through Main.

This cross-Agent artifact is an Execution Delta, not a second Task Contract.
Transmit only Task ID and Status; Changed Files; the actual diff or accessible
diff reference; Commands; a structured Validation Result; Freshness; relevant
current Evidence; Review Input Ready; Unverified Scope; and Residual Risk. Resolve Goal, Acceptance,
Owner, Non-goals, and other existing Authority at its source instead of copying
them here. Keep raw command logs as JIT-readable artifacts and include them only
when a downstream consumer explicitly requires them.

The public Execution Level lines use Core public `execution-level/v2`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Implementation Handoff

## Status

in_progress / blocked / partial / completed

## Task ID

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: implementation-handoff-template.md -->
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: implementation-handoff-template.md -->

## Owner

Authority reference only — do not copy its value into the Execution Delta.

## Result

Use Status and structured Validation Results; do not repeat a narrative.

## Expected Output

Authority reference only — do not copy its value into the Execution Delta.

## Evidence Requirements

Authority reference only — project only consumer-required current Evidence below.

## Changed Files

## Actual Diff or Host-native Diff Reference

Provide actual unified-diff content. A host-native change reference counts only
when the Host dereferences it and supplies a read receipt with exact content
binding to the assigned reviewer, current generation, and changed paths; a
`readable` self-report is insufficient. A digest, summary, prose description,
command output, filename, identifier, or opaque reference is not a diff. Write
`not applicable — no material edits` only when no material edit occurred.

## Commands Run

List command identifiers only. Full logs remain JIT-readable artifacts.

## Validation Results

Use structured command, result, scope, freshness, and proof-limit values.

## Last Material Edit and Validation Ordering

Name the last material edit and the validation run after it. Any material edit
invalidates older validation and review evidence.

## Review Input Ready

Latest Changed Paths:
Exact Reviewable Change Evidence:
Reviewer Artifact Accessibility:
Validation After Latest Material Edit:
Fixed Review Scope:

Normal implementation and repair must provide all five values in the same Implementation Handoff
before review dispatch. Exact evidence is change
content, an exact before/after representation, a reviewer-accessible native
change reference, or an equivalent exact artifact whose actual bytes are
delivered and readable by the assigned reviewer. A changed-file summary,
digest, prose description, command output, filename, opaque reference, or
implementer self-report is not evidence. Static host support is not artifact
readability. Record whether the assigned reviewer can
read the delivered current evidence for its generation and exact paths. Main
forwards the exact payload or reference identity without summarizing or regenerating it. If any value is
missing, remain blocked before review and let the current producer complete the
handoff; do not send a reviewer first.

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

State is `current`, `superseded`, or `invalid`. Repair invalidates only Evidence
whose Scope intersects the repair, Claims that depend on modified behavior, and
transitive impact; unaffected fresh Evidence remains current. Repair requires
fresh validation targeted to affected scope and fresh independent re-review. A
repair supersedes affected Evidence for the previous diff; it does not
supersede unrelated current Evidence.
Current task-agent evidence after the latest material edit uses
`latest-material-edit` and `validation-passed` Claim values.
The Execution Delta transfers only consumer-required `current` rows. Do not
transfer unrelated, `superseded`, or `invalid` Evidence.
Record one `test-approach-selected` Claim for each normal behavior batch with its
Guard G approach, reason, oracle, evidence, and proof boundary. Record current
`red-proof` and `green-proof` only when applicable, with current proof after the
final material edit; they are evidence, not a separate stage. Never fabricate
unavailable proof.

## Unverified Scope

## Residual Risk
```

`not-required` still requires ordinary independent review and digest-only matching
to both lower-risk authorities. Missing or inconsistent authority/binding fails closed
and requires reissue.

Keep the Evidence Ledger task-local, handoff-visible, and non-persistent. Use
no daemon, database, private evidence storage, runtime task state engine, or
hidden protocol record. Include no private prompts, secrets, full logs, hidden
state, or substitute approval verdict.
