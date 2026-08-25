# Review Handoff

The review-agent receives one bounded target and does not edit. Implementation
review requires observable acceptance, the latest actual diff, the declared
changed-path set, current validation results, and the Evidence Requirements.
Main dispatches this assignment only after the producer's Review Input Ready
gate proves exact change evidence is accessible to the reviewer, validation is
later than the latest material edit, and Review scope is fixed. The reviewer
never generates or exports change evidence, repairs the handoff, or mutates the
workspace. Supplied evidence is actual unified-diff content, not a digest,
summary, command output, filename, identifier, or opaque reference. Native
review uses only the delivered current reference that this reviewer can read.

For Analyzed Work, this handoff is a derived projection of the current
Engineering Brief. Protected Brief decisions stay resolvable at their Authority
source; review evidence and findings cannot redefine them. If the handoff
conflicts with the current Brief or a protected decision must change, mark it
blocked and return to analysis through Main.

The `Inbound Review Projection` section contains only Acceptance; Review Boundary;
Effective Level; required Review Skills; required changed scope; the latest
actual diff or accessible reference; current structured validation; relevant
current Evidence; Scope, Freshness, and Proof Limit; and Unverified Scope.
Resolve Goal, Non-goals, Allowed Write Scope, Owner, and other protected
decisions from Authority. Do not send analysis history, the Task DAG, old
validation, unrelated Evidence, or superseded Evidence. Raw logs stay
JIT-readable unless the reviewer explicitly requires one. The remaining
sections are the closing review artifact; they record the review Owner, result,
findings, evidence, reviewed and unreviewed scope, and residual risk.

For implementation or repair review, classify and output Core `Finding Relation`
before severity or blocker. Use only `current-task`, `scope-blocker`, or
`adjacent`; relation grants neither write scope nor Repair authority.
Pre-implementation artifact review is exempt from this implementation-finding
format.

An ordinary finding does not end the Review. The reviewer completes the fixed
Review Boundary's required changed scope, every base dimension, and every
required professional-risk dimension, then returns one Review Handoff with all
evidence-backed findings from that round. A finding never expands the Review
Boundary. Only fundamental architecture, invalid public contract, major
security, or fundamentally unmet Acceptance may return `blocked` early, with
explicit Reviewed and Unreviewed Scope.

Main groups the material `current-task` findings by the existing Review Round
ID and Task ID and emits exactly one canonical Task Contract v2 Repair
assignment per non-empty group. The Task ID stays unchanged. Each finding
separately preserves its Finding Relation, affected scope, Acceptance or risk
impact, required validation, and required covering re-review; the batch also
carries the latest diff and invalidated/reusable Evidence. Main copies the
structured fields without prose inference. Findings from different Task IDs
never share one Repair assignment. A
`scope-blocker` returns blocked through Main to Analysis; `adjacent` is recorded,
does not block, and is ineligible for Repair. Do not re-inject task history. Invalidate
only affected or transitively dependent Evidence; preserve unrelated current
Evidence.

The public Execution Level lines use Core public `execution-level/v2`. The integrity
fallback for missing, malformed, or duplicate public execution-level data is
defined in [execution-level-contract.md](execution-level-contract.md).
Legacy v1 is completed/read only; active or resumed work, edit,
validation, or review requires reissue.

```markdown
# Review Handoff

## Status

in_progress / blocked / partial / completed

## Task ID

## Execution Level

<!-- BEGIN CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: review-handoff-template.md -->
Level: requested=unspecified / L1 / L2 / L3 / L4 / L5; automatic=L1 / L2 / L3 / L4 / L5; minimum=L1 / L2 / L3 / L4 / L5; default=L3; effective=L1 / L2 / L3 / L4 / L5; edit=allowed / blocked
Basis: source=user_fact:<anchor> / analysis_handoff:<anchor>; triggers=["<matched or unknown trigger ID>"] / []; l1=["<false or unknown L1 predicate ID>"] / []; l2=["<false or unknown L2 predicate ID>"] / []; l5=["<false or unknown L5 predicate ID>"] / []; confirmation=not-required / pending / confirmed / rejected / explicit; unresolved=[] / ["unknown-critical-boundary=>L4,edit=blocked"]
L5 Evidence: when=effective L5 only; requires=independent pre-implementation review / strong safety and applicability proof / declared-scope comprehensive negative and failure proof / exhaustive final review
<!-- END CHANGEFORGE CORE PUBLIC EXECUTION TEMPLATE: review-handoff-template.md -->

## Inbound Review Projection

Acceptance:
Review Boundary:
Effective Level:
Required Review Skills:
Required Changed Scope:
Latest Actual Diff or Accessible Reference:
Current Structured Validation:
Relevant Current Evidence:
Scope:
Freshness:
Proof Limit:
Unverified Scope:

## Review Boundary

Review Boundary ID:
Review Strategy:
Review Round ID:
Effective Level:
Required Review Skills:
Specialist Obligations:
Covered Task IDs:
Required Changed Scope:
Professional Risk Dimensions:
Required Validation / Evidence Binding:
Review Assignments:
Primary Close Ordering:

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

For each implementation or repair finding, state fields in this order:

Finding Relation: current-task / scope-blocker / adjacent
Review Round ID:
Task ID:
Severity:
Blocker:
Description:
Affected scope:
Acceptance or risk impact:
Required validation:
Required covering re-review:

Finding Relation appears before severity or blocker. Do not invent private
identifiers; use only the handoff-visible Finding, Review Round, and Task
identities. Pre-implementation artifact review may use its artifact-specific
finding shape without implementation Finding Relation.

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
re-review. Invalidate only Evidence whose Scope intersects the repair, Claims
that depend on modified behavior, and transitive impact. Retain unaffected fresh
Evidence. Expand for a public/shared contract, schema, common abstraction,
ownership/dependency graph, security boundary, transaction/concurrency
semantics, or integration behavior. Focus re-review on the original finding,
repair diff, and affected dependents; an older review cannot cover the new
modification.

Effective Level determines review depth; the Review/Risk Boundary determines
frequency. Task completion is not a Review Boundary. L1-L3 related work uses one
combined independent final review; L4 adds only triggered professional depth;
L5 retains required pre-implementation and final review. A current independent
review subsumes weaker obligations only when its boundary and round identities,
strategy, Effective Level, assignments and required Review Skills, Specialist
obligations, Covered Task IDs, required changed scope, professional-risk
dimensions, current validation/evidence binding, and primary-close ordering
are the same or stronger. Every assignment has exactly one Review Skill and
zero to three review-risk-routed Layer 3 selections. Those selections are
independent from the covered Tasks' implementation Layer 3. Specialists share
the boundary's one Review Round ID, do not close Tasks, and return current
results before the primary emits the sole combined artifact. Every covered
Task completion projection references that artifact's exact identity and
digest. A covering scoped re-review satisfies Final Review without an extra
final round.

Reuse fresh, scope-correct, trustworthy-oracle validation evidence. Reproduce
only for stale evidence, a coverage gap, suspicious oracle/test, flaky/retry,
environment sensitivity, concrete reviewer doubt, or an Effective
Level/professional-risk requirement for independent reproduction.

Only material current-task findings affecting Acceptance, correctness or an
invariant, regression, security/reliability, or material code health require
Repair. Adjacent issues, optional cleanup, style preference, speculative
abstraction, unrelated debt, and future improvement do not enter the mandatory
Repair loop. Ordinary findings remain accumulated while the reviewer finishes
the fixed Review Boundary's required changed scope, base dimensions, and
professional-risk dimensions; the closing handoff reports all evidence-backed
findings from the round. Findings do not expand that boundary. Only fundamental
architecture, invalid public contract, major security, or fundamentally unmet
Acceptance may return `blocked` early after naming Reviewed and Unreviewed
Scope. Every non-fundamental Review outcome, including `findings`, requires the
complete fixed changed scope, base dimensions, and professional-risk dimensions.
`pass` additionally requires no blocking findings.

Main batches material `current-task` findings only when Review Round ID and
Task ID both match. One batch becomes one canonical Task Contract v2 Repair
assignment with the same Task ID and per-finding Finding Relation, affected
scope, Acceptance or risk impact, required validation, and required covering
re-review. Cross-Task batching is forbidden. A `scope-blocker` returns through
Main to Analysis, while an `adjacent` finding is record-only and never enters
Repair.

## Evidence Ledger

| Claim | Owner | Artifact | Command | Result | Freshness | Scope | Proof Limit | State |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Use only `current` evidence. Mark evidence from an older diff `superseded` or
`invalid`. A scoped material edit invalidates validation and review evidence
only for intersecting scope and transitive Task dependencies; unaffected
current evidence remains reusable. Repair requires fresh validation and
re-review of the latest diff.
Only consumer-required current rows enter the downstream repair projection;
noncurrent rows remain excluded.
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
