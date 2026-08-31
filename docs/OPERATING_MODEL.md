# Operating Model

## Source and Built Boundaries

`src/` contains authoring sources: the control model, control prompt, Profile
definitions, registries, Control and Professional Skills, and Layer 3 Skills.
`src/control-model/core-contracts.json` is the authority for roles, Task
Contract v2, Reference Contract v2, Evidence Ledger, completion state, prompt,
Profile, and Control Skill projections. `scripts/build.py` validates those
sources and emits standard artifacts into `dist/`. Installers consume `dist/`
only; build manifests bind the control-model schema and digest.

The Runtime is one fixed Skill surface: 1 Control and 25 Professional
top-level Skills. Foundation capabilities and modifier-only Domains remain JIT
Layer 3 behind the Primary Professional selector and never enter Host top-level
discovery. This Runtime is distinct from the four Agent Profiles below.

This orchestration policy stays within the existing control prompt, four Agent
Profiles, three Skill layers, Execution Levels, and Task Contract v2. It adds no
Profile, Level, Task Contract version, readiness/stabilization state, Analysis
Review Agent, evidence database, runtime state engine, or hook-based control.
The existing Professional Skill Router remains the routing authority.

## Control Flow

```text
request
  -> classify once
  -> Direct Task candidate confirmation or Analyzed Work
  -> one complete initial Analysis and Engineering Brief for Analyzed Work
  -> semantic Tasks with one primary Professional Skill each
  -> edit A -> validate A -> edit B -> validate B
  -> independent review at the minimum sufficient Review/Risk Boundary
  -> scoped repair -> targeted validation -> scoped re-review when required
  -> explicit closure
```

The main agent schedules mechanically and does not inspect source or rewrite analysis-owned business judgments. Analysis, implementation, and review have separate contexts and tool boundaries.

Direct retains one bounded path rather than a third preparation mode. One strong
owner candidate with fixed Professional/Domain/Layer3, semantic scope, and read
boundary enters read-first confirmation at the current Level. The candidate is
not proof. Current source must establish owner, placement, relevant test,
minimum consumer boundary, reuse, and validation before edit. Owner, module,
shared-contract, external-consumer, or material-risk contradiction produces
zero edits and returns through Main for initial Analysis.

For Analyzed Work, the current Engineering Brief is the sole operational
analysis authority. The `analysis-agent` derives it from the request, source,
tests, external evidence, and Specialist input. The Brief owns acceptance,
non-goals, ownership, invariants, placement, contract semantics, rollback, and
a complete Task Contract v2 First Executable Slice. Main dispatches that Slice
verbatim. Task DAGs and later handoffs only split or project the Brief; they do
not select a replacement Slice or rewrite Brief decisions. A conflict returns
blocked through Main to analysis for an updated Brief and redispatch.

Initial Analysis closes observable Acceptance, Owner, Placement, Invariants,
Acceptance-proving Validation, executable dependencies, professional Skill
boundaries, minimum sufficient Review Boundaries, and every critical gap that
could block the First Executable Slice. Once the Brief and next executable Task
are accepted, Task completion or switching, ordinary implementation discovery,
and an unreached Review Boundary do not trigger another Analysis.

The first Analysis is always `initial`. Desired behavior and observable
Acceptance are target authority; observed failure behavior is evidence only.
A Delta is legal only after the complete initial Brief is accepted and current
evidence names the protected decision it invalidates.

New evidence permits Delta Analysis only when it invalidates Acceptance or
Non-goals, Owner/Placement/Invariant, contract or data semantics,
dependency/rollback, material risk, or a scope blocker. The delta covers only the
invalidated decision and its transitive impact on Brief sections, Tasks,
dependencies, Skill assignments, and Review Boundaries. Existing Skill
assignments remain unless the professional domain, work type, or a material-risk
trigger changes. Full re-analysis is reserved for invalidated foundational goals
or system assumptions.

## External Evidence

Only the `analysis-agent` may use `external-read`, and only just in time for a
material unresolved Claim. Supported access is a read-only Web search or fetch,
or an explicitly authorized read-only Connector. Host enforcement is declared
as `native-enforced`, `sandbox-enforced`, `prompt-enforced`, or `unsupported`;
general network access is not equivalent to safe external read.

External content is untrusted evidence, never a control instruction. The
analysis agent normalizes relevant facts into Claims, records their sources in
the existing Evidence Ledger, and makes the resulting decision in the Brief.
Queries and requests use only the minimum public information and exclude
private source, credentials, sensitive data, internal identifiers, and
proprietary content. An unsupported host continues when existing evidence is
sufficient. A missing non-critical fact becomes a Proof Limit; an unobtainable
critical fact that can invalidate the Slice triggers `unknown-critical-boundary`
and blocks implementation dispatch.

## Task, Validation, and Review Boundaries

The Current Task Boundary is Goal plus Acceptance plus Non-goals. Allowed Read
Scope permits inspection and discovery. Allowed Write Scope is the maximum edit
permission, not a repair checklist, and completion does not require a clean
repository.

A Task is one complete, understandable, acceptable, and verifiable semantic
change with one Primary Professional Skill. Work that jointly satisfies one
Acceptance, must take effect together, and naturally validates together stays in
one Task. A materially different professional domain remains a separate Task;
files, functions, code layers, tests, and edit steps do not by themselves create
Task boundaries. Review Boundaries are independent of these Task and Skill
boundaries.

Route evidence and Level evidence remain independent. Existing atomic task
facts may be reused, but routing candidates and route conclusions cannot prove
Level predicates; each proven fact kind binds only its corresponding predicate.
Material floors, historical maxima, recomputation, and non-bypassable controls
still dominate the result.

Declared Host/Profile capability is static configuration, not runtime truth.
Dispatch uses invocation-scoped effective capability and fails closed on absent
or unknown facts. Semantic Role stays fixed while a proven Host Executor may be
replaced, carrying Professional Skill, Layer3, Level/Basis/history, scope,
acceptance, validation, review, handoff, and stop conditions unchanged. Main
never absorbs implementation work when no executor is available.

Task completion records progress only; it does not by itself trigger Analysis,
Review, replanning, or user confirmation. Related Tasks inside one Review
Boundary execute continuously, and the Task Agent runs targeted validation after
each Task's final material edit. Fresh, scope-correct evidence with a trustworthy
oracle remains reusable. Independent review does not mechanically repeat the
same checks unless evidence is stale, coverage is missing, the oracle or test is
suspicious, a result is flaky or environment-sensitive, the reviewer has a
concrete doubt, or Effective Level or professional risk requires independent
reproduction.

Every discovered issue is classified before severity or blocker status:

- `current-task`: required by the current boundary and eligible for blocking repair.
- `scope-blocker`: required for completion but needs a new scope or analysis decision; return through Main to analysis.
- `adjacent`: real but unnecessary for the current task; record residual risk and continue without repair.

Severity does not grant scope authority. Review, validation, and same-pattern
scans may read callers, consumers, siblings, and configuration to prove the
current change, but discovery alone never authorizes repair. Only material
current-task findings that affect Acceptance, correctness or an invariant,
regression, security or reliability, or material code health require Repair.
Adjacent issues, optional cleanup, style preferences, speculative abstractions,
unrelated technical debt, and future improvements remain outside the mandatory
Repair loop. All current-task same-pattern occurrences inside authorized scope
remain mandatory; adjacent matches are recorded with rationale and residual
risk.

An ordinary material finding does not end the current review or expand its
fixed boundary. The reviewer continues through all required changed scope,
base dimensions, and professional-risk dimensions and returns every
evidence-backed finding from that round together. Early `blocked` review is
limited to a fundamental architecture error, invalid public contract, major
security defect, or fundamentally unmet Acceptance and names both Reviewed and
Unreviewed Scope.

Main batches all material `current-task` findings that share one Review Round
and Task ID into exactly one canonical Repair Task Contract, retaining the
original Task ID. The assignment preserves each finding's relation, affected
scope, Acceptance or risk impact, required validation, and required covering
re-review. It never merges Task IDs: `scope-blocker` returns through Main to
Analysis, while `adjacent` remains recorded and deferred outside Repair.

Effective Level determines review depth; the minimum sufficient Review or Risk
Boundary determines frequency. L1-L3 related changed scope defaults to one
combined independent final review of the latest actual diff and all required
changed files. L4 adds only triggered professional gates or specialist depth,
not automatic rounds. L5 retains independent pre-implementation and final
review, declared-scope negative and failure proof, and exhaustive final depth.
Intermediate Review Boundaries require a concrete risk such as a downstream
public API/schema/protocol dependency, migration or irreversible data,
security/privacy, transaction/concurrency/persistence invariants, material
downstream rework, an independent integration boundary, or an L5 or explicit
professional gate. Task completion alone is never such a boundary.
Task, edit, and file counts do not otherwise determine Review frequency.

Normal Task closure is one sequence: final edit, fresh validation, exact change
capture, the same Task's Implementation Handoff, and Main's readiness gate.
Supplied review evidence contains the unified diff itself; native review uses a
current reference binding the assigned reviewer, current generation, exact
changed paths, and a readable delivered instance. A static capability,
digest, path, summary, or command-output label cannot establish readiness.

A current Review Boundary carries one boundary and Review Round ID, strategy,
Effective Level, required Review Skills, Specialist obligations, Covered Task
IDs, non-empty Required Changed Scope, Professional Risk Dimensions, current
Validation / Evidence Binding, assignments, and primary-close ordering. It has
exactly one primary and zero or more specialist review-agent assignments. Each
assignment has one ID, role, exactly one registered Review Skill, zero to three
unique Layer 3 selections routed by that Skill from review risk, and bounded
scope. Review Layer 3 is independent from covered Tasks' implementation Layer
3. All assignments share the one round. Specialists neither add rounds nor
close Tasks; the primary waits for every current required specialist result and
emits the sole artifact binding boundary, round, covered Tasks, changed and
evidence scope, current Task generations, assignment results, and verdict.
Every covered Task completion projection references that exact artifact
identity and digest. A fresh independent review subsumes weaker equivalent
obligations only when these dimensions are the same or stronger.

Any scoped material edit invalidates current validation and review evidence
only for intersecting scope and downstream transitive Task dependencies;
unaffected current evidence remains reusable. After Repair, fresh targeted
validation over required changed scope and fresh independent re-review of the
latest post-repair diff and evidence remain mandatory for that affected scope;
pre-repair validation and review cannot satisfy readiness. Re-review focuses on
the original finding, the
Repair diff, and affected dependents; it expands for a public/shared contract,
schema, common abstraction, ownership or dependency graph, security boundary,
transaction/concurrency semantics, or integration behavior. A scoped re-review
that covers the final current obligation also satisfies Final Review without an
extra round.

## Skill Layers

- Control: one Skill for task classification, dispatch, progress, review/repair routing, and closure.
- Professional: complete AI-facing engineering judgment for one work type.
- Foundation/Domain: narrow, high-density rules loaded only for triggered decisions.

Each Task keeps its own Primary Professional Skill and implementation Layer 3.
Task DAG nodes retain only required Review Skills, Specialist obligations, and
professional-risk dimensions. Review strategy, frequency, assignment
scheduling, round identity, and primary-close ordering live only on the global
Review Boundary. Combined review never collapses distinct professional work
into one oversized Task or one Skill.

Registries declare role support, trigger and anti-trigger signals, required inputs, output contract, escalation signals, and reference index. They contain no private execution-state fields.

Executable tasks and handoffs use the exact schema in the managed Core Contract
Projection below. DAG nodes additionally name `Dependencies`.

## Evidence

Engineering evidence stays observable in handoffs and is never persisted as
private runtime state. Each entry names its evidence-producing agent, freshness,
scope, and proof limit. Implementation completion binds freshness to a current
task-owner claim and current review-agent claims for the latest changed scope.
Evidence is reused while fresh, scope-correct, and supported by a trustworthy
oracle. A material edit applies the intersecting and transitive dependent
invalidation boundary described above rather than invalidating unaffected
current evidence.

## Core Contract Projection

<!-- BEGIN CHANGEFORGE CORE DOCS PROJECTION: operating-model-task-evidence-completion -->
Contract identities:

- Task Contract v2
- visible task-local Evidence Ledger
- completed is terminal for its Task ID

Task Contract v2 fields (exact order):

1. `Task ID`
2. `Status`
3. `Goal`
4. `Owner`
5. `Inputs`
6. `Allowed Read Scope`
7. `Allowed Write Scope`
8. `Non-goals`
9. `Expected Output`
10. `Acceptance`
11. `Verification`
12. `Evidence Requirements`
13. `Parallel Safety`
14. `Workspace Requirement`
15. `Integration Owner`
16. `Review Owner`
17. `Stop Conditions`

New task assignment initial Status:

`in_progress`

visible task-local Evidence Ledger fields (exact order):

1. `Claim`
2. `Owner`
3. `Artifact`
4. `Command`
5. `Result`
6. `Freshness`
7. `Scope`
8. `Proof Limit`
9. `State`

same Task ID transitions (exact):

```text
in_progress -> blocked | partial | completed
blocked -> in_progress | partial | completed
partial -> in_progress | blocked | completed
```

fail-closed outcomes (exact):

```text
validation-failed -> blocked | partial
validation-unavailable -> blocked | partial
high-risk-review-missing -> blocked | partial
blocking-finding-unresolved -> blocked
changed-scope-unreviewed -> blocked | partial
evidence-stale-after-edit -> in_progress | blocked | partial
```

No transition leaves completed for that Task ID.
New work after completion starts `in_progress` under a new Task ID.
<!-- END CHANGEFORGE CORE DOCS PROJECTION: operating-model-task-evidence-completion -->
