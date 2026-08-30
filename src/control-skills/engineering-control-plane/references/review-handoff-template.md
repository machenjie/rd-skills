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
blocked, report Reviewed Scope, Unreviewed Scope, and the current Proof Limit,
and return to analysis through Main.

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

A supplied path, symbol, or owner is an exact selector, not owner proof.
Review reads it first and stops discovery when current source confirms the
role. A same-owner/route/contract locator correction may preserve a valid
finding but cannot change the Brief or route; a protected owner, placement, or
contract contradiction returns through Main. Without an accepted Brief this
requests initial Analysis; only invalidation of an accepted Brief's protected
decision requests bounded Delta. Review never reroutes, changes the Brief, or
repairs from a locator alone.

For implementation or repair review, classify and output Core `Finding Relation`
before severity or blocker. Use only `current-task`, `scope-blocker`, or
`adjacent`; relation grants neither write scope nor Repair authority.
Pre-implementation artifact review is exempt from this implementation-finding
format.

An ordinary finding does not end the Review. Initial Review completes the fixed
Review Boundary's required changed scope, every base dimension, and every
required professional-risk dimension, then returns one Review Handoff with all
evidence-backed findings from that round. Re-review is focused only on inherited
finding resolution, repair-diff correctness, repair regressions, repair-affected
scope and transitive dependents, and whether the frozen Acceptance, Invariant,
Contract, and professional-risk boundary still holds. A finding never expands
the Review Boundary. Only fundamental architecture, invalid
public contract, major security, or fundamentally unmet Acceptance may return
`blocked` early, with explicit Reviewed and Unreviewed Scope. After Review
Input Ready dispatch, `blocked` is also allowed only when required review
evidence or surface becomes unavailable, required current evidence becomes
stale, or current evidence invalidates protected Authority or the Engineering
Brief. Report non-empty Reviewed Scope, Unreviewed Scope, and Proof Limit.
Ordinary uncertainty, difficulty, findings, and continuable gaps do not qualify;
protected invalidation returns through Main to Analysis.
Delta Analysis invalidates validation and review evidence for every affected
Task and transitive dependent. Completion then requires an affected Task edit,
fresh post-edit validation, and a fresh focused PASS re-review; pre-decision
evidence cannot close the changed protected decision.

Classify every Re-review finding as `inherited`, `repair-regression`,
`frozen-boundary-violation`, `protected-invalidation`, or `adjacent`, and project
that classification to the existing Finding Relation. `inherited`,
`repair-regression`, and an evidence-backed `frozen-boundary-violation` may be
material `current-task` blockers. `protected-invalidation` is a `scope-blocker`
and returns through Main to Delta Analysis. `adjacent` is residual/follow-up
only, cannot block, and never enters Repair. A Re-review discovery is not
mandatory current-task work without this classification and evidence.
Every Re-review finding must expose non-empty `Re-review Classification` and
`Classification Evidence` fields. A `frozen-boundary-violation` requires
explicit Classification Evidence that identifies the violated frozen
Acceptance, Invariant, Contract, or professional-risk boundary. Initial Review
may omit both fields or use `not-applicable`; Main consumes these structured
fields without prose inference.

When the Primary Review supplies `Canonical Findings`, those are the material
findings consumed by the existing grouping rule. Semantic reconciliation is
complete before handoff; Main copies the structured fields without semantic
reconciliation or prose inference.

Main groups the material `current-task` findings by the existing Review Round
ID and Task ID and emits exactly one canonical Task Contract v2 Repair
assignment per non-empty group. The Task ID stays unchanged. Each finding
separately preserves its Finding Relation, affected scope, Acceptance or risk
impact, required validation, and required covering re-review; the batch also
carries the latest diff and invalidated/reusable Evidence. Main copies the
structured fields without prose inference. Findings from different Task IDs
never share one Repair assignment. A
`scope-blocker` from review or re-review returns blocked through Main to
Analysis; `adjacent` is recorded, does not block, and is ineligible for Repair.
Do not re-inject task history. Invalidate
only affected or transitively dependent Evidence; preserve unrelated current
Evidence.

Main permits at most two automatic Repair rounds for each Task ID. Review
Boundary ID, Review Round ID, and Delta Analysis do not reset that budget. At
the cap, an unresolved blocker returns `BLOCKED / non-converged`; protected
invalidation returns through Main to Delta Analysis; adjacent or hardening-only
work may be recorded while the current completion contract closes. The cap
never implies `pass`. Repeated review-driven Delta Analysis must change
hypothesis, material, gap, or transition after two same-path failures; a third
unchanged replan is forbidden and returns Main or blocks.

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

Finding Identity:
Finding Relation: current-task / scope-blocker / adjacent
Re-review Classification: inherited / repair-regression / frozen-boundary-violation / protected-invalidation / adjacent / not-applicable for Initial Review
Classification Evidence:
Review Round ID:
Task ID:
Category:
Repair required: true / false
Severity:
Blocker:
Description:
Protected Decision Boundary:
Defect:
Violated invariant:
Failure mechanism:
Fix path:
Source reviewer evidence:
Affected scope:
Acceptance or risk impact:
Required validation:
Required covering re-review:
Freshness:
Proof Limit:

Re-review findings require both classification fields; Initial Review may omit
them or mark `Re-review Classification: not-applicable`.
frozen-boundary-violation requires explicit Classification Evidence. Finding
Relation appears before severity or blocker. Do not invent private
identifiers; use only the handoff-visible Finding, Review Round, and Task
identities. Pre-implementation artifact review may use its artifact-specific
finding shape without implementation Finding Relation.

## Canonical Findings

The Primary Review compiles this section only after it completes the fixed
Review Boundary and consumes every current required primary and specialist
result. Partition raw findings by Task ID, Review Round ID, Finding Relation,
and Protected Decision Boundary. Within one partition, perform deterministic
stable exact dedup first. Merge different wording only when current source
evidence establishes the same defect, same violated invariant, same failure mechanism, and same fix path. Otherwise keep findings separate. A partition
boundary, location alone, or model confidence alone is insufficient merge
evidence. Evidence-backed findings remain present regardless of confidence.

Preserve every source Finding entry, source reviewer evidence item, affected scope,
Acceptance or risk impact, required validation, required covering re-review,
freshness statement, and proof limit. `adjacent` remains record-only;
`scope-blocker` remains on the Main/Delta Analysis route. Repair input is
limited to material `current-task` canonical findings under the existing one
Repair batch. Main copies canonical findings without semantic reconciliation
or prose inference. This compiler adds neither a Validator Agent nor a Review
stage. Verification batching is permitted when the existing contract already
requires independent verification or reproduction and all findings share that
bounded boundary.

For each canonical finding, state fields in this order:

Canonical Finding:
Source Findings:
Task ID:
Review Round ID:
Finding Relation: current-task / scope-blocker / adjacent
Protected Decision Boundary:
Categories:
Descriptions:
Defect:
Violated invariant:
Failure mechanism:
Fix path:
Source reviewer evidence:
Affected scope:
Acceptance or risk impacts:
Required validation:
Required covering re-review:
Freshness:
Proof Limits:
Repair required: true / false

## Semantic Repair Convergence

Include this section only when the current handoff closes a Repair/Re-review
trajectory. Classify the trajectory's canonical findings as `progressing`,
`bounded-class`, `oscillating`, or `indeterminate` from current source evidence.
`progressing` requires every inherited finding to be resolved, every current
finding to be an independently evidenced defect, and no verified invariant to
be rebroken. `bounded-class` requires the same violated invariant, failure
mechanism, and treatment across a current-source-proven finite sibling set
inside the original Task scope and protected decision boundary. Use
`oscillating` only for an evidenced A→B→A canonical failure set, an evidenced
rebreak of a previously verified invariant, or an explicitly evidenced failure
set cycle. Otherwise use `indeterminate` and preserve existing behavior.

A single repeated finding, unchanged finding count, a new finding, unchanged
severity/category, or another edit to the same file does not by itself prove
oscillation. `progressing` only continues the existing path. `bounded-class`
may reshape the next existing Repair into one finite class-wide batch.
`oscillating` may block the same non-converging path. The classification has no PASS authority,
does not reroute, and adds no Agent, Review/Repair round,
validation stage, persistent state, or normal no-finding-path work.

State the current Task ID, original Task scope, protected decision boundary,
canonical finding history, inherited-resolution evidence, independent-new-
defect evidence, finite sibling scope when proven, rebroken-invariant evidence,
explicit cycle evidence, classification, disposition, and proof limit.

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
semantics, or integration behavior. Focus re-review on inherited finding
resolution, repair-diff correctness, repair regressions, affected transitive
dependents, and the frozen Acceptance, Invariant, Contract, and professional-risk
boundary; an older review cannot cover the new modification. A re-review
completes a Review Round. Classify each new finding as `inherited`,
`repair-regression`, `frozen-boundary-violation`, `protected-invalidation`, or
`adjacent` before applying the existing Finding Relation.

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
Repair loop. Ordinary findings remain accumulated during Initial Review while
the reviewer finishes the fixed Review Boundary's required changed scope, base
dimensions, and professional-risk dimensions. Focused Re-review completes only
its frozen five-part scope and explicitly records that the frozen
professional-risk boundary remains valid; it does not reopen Initial Review
scope or require Initial completeness fields. The closing handoff reports all evidence-backed
findings from the round. Findings do not expand that boundary. Only fundamental architecture, invalid public contract, major
security, or fundamentally unmet Acceptance may return `blocked` early after
naming Reviewed and Unreviewed Scope. After ready dispatch, only unavailable
required review surface, stale required current evidence, or protected
Authority/Engineering Brief invalidation may also block; record Reviewed Scope,
Unreviewed Scope, and Proof Limit, and route protected invalidation through Main
to Analysis. Ordinary uncertainty, difficulty, findings, and continuable gaps
never early-block. Every other Initial Review outcome, including `findings`,
requires the complete fixed changed scope, base dimensions, and
professional-risk dimensions. A focused Re-review outcome instead requires its
five frozen checks and explicit frozen professional-risk validity. `pass`
additionally requires no blocking findings.

Main batches material `current-task` findings only when Review Round ID and
Task ID both match. One batch becomes one canonical Task Contract v2 Repair
assignment with the same Task ID and per-finding Finding Relation, affected
scope, Acceptance or risk impact, required validation, and required covering
re-review. Cross-Task batching is forbidden. A `scope-blocker` closing review or
re-review returns through Main to Analysis, while an `adjacent` finding is
record-only and never enters Repair. A re-review completes its Review Round;
any inherited, repair-regression, or evidence-backed frozen-boundary violation
mapped to a material `current-task` finding forms the next same-Task Repair
batch, followed by fresh validation and another fresh re-review, while the
per-Task maximum remains two automatic Repair rounds. Delta Analysis does not
reset the budget. At cap, blockers fail closed as non-converged; protected
invalidation routes to Main/Delta Analysis; adjacent/hardening stays residual.

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
