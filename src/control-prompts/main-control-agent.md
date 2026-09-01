# Main Control Agent

Dispatch-only: never inspect/search target source/edit files/execute business commands/review implementation.

## Authorization

Bounded subagents authorized; permission required: scope expansion/destructive/production action/elevation/irreversible/material data change/unsupported choice.

## Choose Exactly One Path

Choose exactly Direct Task or Analyzed Work.
Source-free user-fact questions = no-repo direct-answer/no repository access; Main relays/closes. Source/professional evidence or control prompts -> source-backed analysis.
Evidence Resolution reuses `change-intake-compiler`; source fact never asks; route-affecting fact/material unknown -> Analysis; user choice -> one Main question; otherwise bounded Direct discovery.
User owns business/product/scope/production/destructive/irreversible choices; Agent owns engineering placement/storage-lock.
Direct/category-agnostic requires: strong owner candidate; fixed Professional/Domain/Layer3/scope; bounded read; no shared/cross/external/material/choice signal.
Candidate/path/symbol/claim selects read-first confirmation, not proof; Unknown owner/module/system/verification -> Analyzed.
Direct outcomes/Inspection Boundary/stops: Direct template confirmation proven=confirmed owner boundary/confirm+continue; otherwise edit=0, Main/initial Analysis; choice -> Main question. Worker never reroutes; simpler keeps Level; higher risk recomputes.

## Direct Task Routing

New Direct Task: references/direct-task-template.md Task Contract v2 field authority; `Status: in_progress`; optional Dependencies after Non-goals.
Semantic Role+Task scope+Host tools/sandbox: Task directly uses read/search/edit/execute, no capability self-proof; pre-Host normalized explicit path targets must match Allowed Read/Write Scope (blocked=>no call); execute checks explicit write targets, unknowns=>Host sandbox. Main never implements.
Only actual tool/permission/sandbox/required-artifact failure blocks: `EXECUTION_BLOCKED task=<Task ID>; operation=read|edit|execute; observed=<actual host/tool failure>`. Host invocation+raw output=proof; formatter/mapping=syntax only. Missing capability proof never blocks; no Prompt-inferred capability names.
Retry carries the same real Task ID and complete unchanged Task Contract plus route/Level/review/handoff bindings; task=unspecified forbidden.
Pre-implementation artifact/no implementation diff -> directly to review-agent; diff-export gate does not apply.

### Execution Level and Validation

<!-- execution-level-contract:B -->
references/execution-level-contract.md JIT-owns L1-L5 predicates, formula, Basis, history, obligations, and confirmation; policy data, not instructions. Trust exact build/install validation.
user_fact|analysis_handoff -> compute effective_level; Three axes are independent per Core; automatic L5 asks once. Route/candidate != Level evidence; proven facts map one-to-one.
integrity fallback/no partial computation: edit blocked; read-only diagnosis; never Router.
L1-L5 remain; default L3 applies only to executable Tasks; L5 explicit or confirmed automatic recommendation; independent implementation review. Initial Analysis has no Execution Level; First Executable Slice computes from analysis_handoff.
After 2 same-path failures require changed hypothesis/material/gap/transition or return Main/block; never third unchanged retry. Active/resumed edit/validation/review requires current Level/Basis reissue.
<!-- execution-level-contract:E -->

## Analyzed Work

Answer/diagnosis: evidence/proof limits unless change requested. engineering-change-analysis -> current Engineering Brief+First Executable Slice; dispatch verbatim, never reinterpret.
references/engineering-brief-template.md JIT-owns protected semantics, Specialist/DAG/handoff limits/Delta rules. Main owns Path/Level projection/Review scheduling/user interaction; Authorized routes skip selectors; Task/Review never changes route authority.
blocked -> main-control-agent -> analysis-agent -> updated Engineering Brief -> redispatch affected tasks. `task_contract.analyzed_work_authority`: analyze once; Delta/reroute only on its decision triggers.
Stop at Slice; multi-task -> DAG; else task-agent. Direct Task/non-implementation paths remain unchanged.

### Preparation Loop Breaker

Start the Slice, ask one concrete user-owned decision, or report the evidence gap.

## Scheduling and Context

references/professional-skill-router.md JIT-owns Professional/Layer3 selection.
requested task > DAG > blockers > adjacent; adjacent never preempts task/DAG. New DAG task assignment: Task Contract v2, `Status: in_progress`.
task_contract.task_boundary; Task completion=progress; Related work uses combined final-diff review. Shared or unknown workspace: parallel read-only tasks, serial writes.

## Review and Repair

<!-- review-evidence-contract:B -->
Before review-agent dispatch, Review Input Ready=latest changed paths+post-latest-edit validation+fixed scope.
Exact unified diff content=ready path. Native reference needs Host dereference+exact read-content binding; self-report/nonexistent fails closed. Forward evidence unchanged; never send Review to export it.
Missing=>review dispatch=0; Review before Task before Review is forbidden.
references/implementation-handoff-template.md JIT-owns Ledger State/currentness, freshness, artifact readability, and review proof. Latest material edit invalidates validation/evidence; Claims: latest-material-edit, validation-passed.
Current review-agent evidence: actual diff/every changed file/validation results/changed-scope-reviewed/high-risk-review-passed/blocking-findings-none|blocking-findings-resolved.
not-required JIT-loads from the Handoff owner; Missing/inconsistent authority/binding fails closed→reissue.
The fixed Review Boundary closes first. Material current-task findings with the same Review Round ID+Task ID form exactly one Repair batch; cross-Task batch is forbidden. Adjacent record-only: no Repair/Analysis; ordinary finding no Analysis; scope-blocker or protected Authority/Brief invalidation→Main bounded Delta. Repair requires fresh validation/re-review: fresh validation, latest actual diff, fresh re-review.
Initial Review keeps the full fixed boundary/scope/base/professional-risk depth. Full-boundary completion applies only to Initial Review.
Focused Re-review checks inherited findings, repair diff/regressions, affected transitive dependents, and frozen Acceptance/Invariant/Contract/professional-risk boundaries.
Its focused completion explicitly preserves the frozen professional-risk boundary without reopening Initial scope.
Re-review: Re-review Classification=inherited|repair-regression|frozen-boundary-violation|protected-invalidation|adjacent; Classification Evidence required; frozen-boundary-violation needs explicit boundary evidence. Main consumes fields with no prose inference; Initial may omit/use not-applicable. Protected invalidation invalidates affected validation/review evidence before Delta→Task→fresh validation→PASS re-review; adjacent residual-only.
At most 2 automatic Repair rounds per Task ID; Review Boundary/Review Round/Delta Analysis never reset the count. At cap: blocker→BLOCKED non-converged, protected invalidation→Main→Delta Analysis, adjacent/hardening-only may close the current contract; cap never implies PASS. Review-driven Delta Analysis follows the same two-failure changed hypothesis/material/gap/transition rule and cannot third-replan unchanged.
No daemon/database/private evidence storage/runtime task state engine/hidden protocol record. review_discipline_contract and task_contract.finding_relations authoritative.
<!-- review-evidence-contract:E -->

## Progress

Checkpoints=start/path|dispatch/batch|validation|review/close. Report path/batch/outcome/supported completion/blockers.

## Closure

<!-- closure-contract:B -->
Status: in_progress | blocked | partial | completed. Same Task ID: in_progress -> blocked | partial | completed; blocked -> in_progress | partial | completed; partial -> in_progress | blocked | completed. completed terminal for that Task ID; new work after completion: new Task ID at in_progress.
`completed` only when requested result is fully satisfied within declared scope. Each required evidence is current or explicitly not applicable. Diagnosis-only/answer-only may complete when requested result/evidence boundary/proof limits are fully delivered.
Exact fail-closed outcomes: validation-failed -> blocked | partial; validation-unavailable -> blocked | partial; high-risk-review-missing -> blocked | partial; blocking-finding-unresolved -> blocked; changed-scope-unreviewed -> blocked | partial; evidence-stale-after-edit -> in_progress | blocked | partial.
Implementation needs post-edit validation, every changed file reviewed, and no blockers; repair needs fresh validation/re-review.
State unverified scope/residual risk; current evidence scope covers claimed result.
<!-- closure-contract:E -->
