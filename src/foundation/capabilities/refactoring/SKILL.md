---
name: refactoring
description: Guides behavior-preserving code reshaping with characterization tests for risky changes and explicit handling of boundaries, contracts, rollback, graph/memory freshness, validation evidence, split/merge safety, and cleanup exits.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "79"
changeforge_version: 0.1.0
---

# Mission

**Improve code structure while provably preserving observable behavior** — using characterization tests before reshaping risky code, keeping steps small enough to review and revert independently, protecting public contracts and persistence boundaries, and making every behavior change an explicit, separately approved decision rather than an inadvertent side effect of structural movement.

# When To Use

Use this capability when: simplifying a method, class, file, or module that has accumulated mixed responsibilities over time; extracting a reusable abstraction from duplicated logic; merging small files that lack independent boundaries back into their owner; splitting behavior by real owner, lifecycle, invariant, side effect, public contract, or test boundary; renaming concepts to align with the current domain model; reducing coupling between modules to enable independent testing or deployment; removing dead code or obsolete abstractions; preparing a codebase section for a future behavior change by isolating dependencies first; or when a code review flags "this is hard to read" or "this is fragile" without requiring behavior change.

# Do Not Use When

Do not use this capability to: change observable behavior and label it as a refactor ("I just cleaned it up" while changing return values, validation logic, or error handling); rewrite stable, correct, well-tested code in a different style or paradigm purely out of preference; churn public API contracts, database column names, configuration keys, or metric names without a compatibility plan and consumer impact review; or optimize for performance (use `profiling` to identify the bottleneck first; optimization changes are not structure-only — they require before/after measurement).

# Stage Fit

Use during refactoring planning, implementation, bug-fix repair, code-review, validation, and handoff when structure changes but behavior should remain stable. Per-stage focus:

- **refactoring**: behavior-preserving extract/move/inline/merge/split; characterization tests; rollback path.
- **bug-fix**: apply structural change only when the verified root cause requires it.
- **code-review**: confirm the refactor preserved public behavior with test evidence.
- **validation/handoff**: reconcile graph, memory, changed paths, validation freshness, rollback, and residual risk.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Extract/move/inline local structure | Function, method, class, helper, or file movement with no intended behavior change. | Preserve observable behavior while improving ownership and readability. | Behavior boundary, owner decision, before/after tests, rollback step. | `implementation-structure-design`, `code-review` | Public API redesign. |
| Split or merge files/modules | Large file/object split, small-file merge, module move, import/export reshaping. | Keep public contracts, dependency direction, side effects, and tests visible. | Import/export diff, dependency-rule check, behavior tests before/after. | `module-boundary-design`, `architecture-enforcement-tooling` | File-count preference as rationale. |
| Risky behavior seam refactor | Untested, complex, auth, money, data integrity, concurrency, or external side-effect code. | Add characterization tests before movement and preserve failure semantics. | Characterization cases, negative/denied paths, mutation-like assertion quality. | `quality-test-gate`, `regression-testing` | Refactor first, test later. |
| Cleanup inside refactor | Dead code, stale abstraction, deprecated branch, feature flag, compatibility shim. | Separate deletion safety from movement and give cleanup an owner/expiry. | Caller search, removal condition, cleanup issue, old/new tests, rollback. | `cleanup-deletion-governance`, `minimal-correct-implementation` | Silent deletion as cleanup. |
| Graph/memory/evidence review | Prior incident note, stale memory, generated reference, reflection, dynamic caller, validation drift. | Confirm current source and generated/runtime graph before accepting equivalence. | Accepted/rejected memory, graph search scope, changed-path validator map. | `repository-graph-analysis`, `validation-broker` | Trusting old context. |

# Non-Negotiable Rules

- **Refactoring must preserve observable behavior unless a behavior change is explicitly approved, documented, and reviewed as a separate step.** "Observable behavior" means: the outputs produced for the same inputs (function return values, API response shapes, database mutations, emitted events, side effects visible to callers). Internal representation changes (private field names, local variable renaming, private method extraction) are not observable. Changing a `null` return to an empty array is observable — it is a behavior change, not a refactor.
- **Risky refactoring requires characterization tests before structural changes begin.** "Risky" means: the code under change is not covered by tests; the code has complex control flow, concurrency, or state management; the code touches authorization, financial calculations, or data integrity; or the code interacts with external systems. Characterization tests (Michael Feathers "Working Effectively with Legacy Code") — tests that capture current behavior, even if that behavior is imperfect — are the safety net that makes structural changes reviewable.
- **Each refactoring step must be reviewable and revertable independently.** Large refactors committed in a single 2,000-line diff are not reviewable — reviewers cannot distinguish behavior-preserving movement from accidental change. Rule: each step must be a logical unit that passes all tests independently. Rename and move classes in separate commits from changing their logic. Extraction and injection in separate commits. If git bisect cannot identify which step introduced a regression, the steps were too large.
- **Public contracts must not change without a compatibility plan.** Public contracts include: API endpoint request/response shapes, gRPC/OpenAPI/AsyncAPI schemas, configuration keys and environment variable names, database column names and table structures, event/message payload schemas, public library function signatures, metric and log field names. Changing any of these is not a refactor — it is a breaking change requiring versioning, migration, or consumer coordination.
- **Formatting changes must not be mixed with semantic changes in the same commit.** A commit that reformats 400 lines of code while also changing 3 lines of logic makes it impossible to review the logical change. Rule: formatting-only commits are separate from logic-movement commits. Use automated formatters (prettier, black, gofmt) to separate formatting from semantic changes completely.
- **Refactoring must not be used to smuggle performance optimizations without measurement.** "I refactored this to be more efficient" while changing an O(n²) algorithm to O(n log n) is a behavior-change-adjacent optimization, not a pure structural change. Optimization requires baseline measurement and validation. Refactor and optimize in separate changes.
- **Authorization, financial calculations, and data integrity logic must have behavior-equivalence tests before any structural change.** These are the highest-risk code categories. A refactoring mistake in an authorization check can introduce a privilege escalation. A refactoring mistake in a financial calculation can produce incorrect totals. Extract characterization tests that cover all branches before touching these areas.
- **Large object, large file, and large module refactors need an explicit split target.** Splitting is not complete until the new object, file, or module ownership and relationship type are named.
- **File split and file merge refactors must preserve observable behavior.** Moving code between files, merging helper files into an owner, or splitting a large file cannot change return values, emitted events, persistence effects, ordering, errors, logs that consumers rely on, public exports, or side effects unless that behavior change is separately approved.
- **Merge and split steps must preserve public contracts and dependency direction.** Import/export changes are allowed only when callers, public APIs, test boundaries, generated references, and layer rules are inspected and updated without hiding side effects.
- **Do not change behavior while moving or merging files.** File movement, import cleanup, visibility changes, private helper inlining, and public behavior edits must be separate reviewable steps.
- **Cleanup is part of refactoring, not optional polish.** Dead code, deprecated APIs, stale compatibility branches, and expired feature flags require owner, expiry, removal sequence, and behavior preservation evidence.
- **A refactor must prove complexity decreased or explain why it did not.** Before/after evidence can be cognitive complexity, branch count, dependency count, public API surface, collaborator count, directory density, or test readability.

# Industry Benchmarks

Anchor against Fowler's named refactorings, Feathers-style characterization tests and seams, Beck small steps, SemVer public-contract discipline, architecture-rule enforcement, git-bisectable commits, mutation testing, and cognitive-complexity reduction. Keep deep mechanics, risk classification, step discipline, and anti-examples in [references/checklist.md](references/checklist.md) so the body stays focused on trigger, routing, evidence, and closure rules.

# Selection Rules

Select this capability when **structural improvement is the primary goal and behavior must be preserved**. Route elsewhere when: `code-review` is primary (evaluating an existing diff for correctness and review feedback); `module-boundary-design` is primary (deciding what the target architecture should be — use that first, then refactor toward it); `test-strategy` is primary (defining what tests are needed for new functionality — not preserving existing behavior); `profiling` is primary (measuring and reducing performance bottleneck — optimize after refactoring, not during); `api-contract-design` is primary (changing a public API contract — that is a breaking change, not a refactoring).

# Proactive Professional Triggers

- **Signal:** A refactor moves, extracts, inlines, renames, splits, or merges code without an explicit observable behavior boundary.
  **Hidden risk:** behavior changes are hidden inside structural movement and reviewers cannot tell whether outputs, side effects, ordering, or errors changed.
  **Required professional action:** define behavior boundary and split intentional behavior changes into separate work.
  **Route to:** `implementation-structure-design`, `code-review`.
  **Evidence required:** preserved outputs/side effects list, excluded behavior-change work item, before/after test command, and rollback step.
- **Signal:** Untested, branch-heavy, auth, money, data-integrity, concurrency, or external side-effect code is refactored before characterization tests.
  **Hidden risk:** a mechanical extraction creates silent wrong behavior in a critical branch with no failing signal.
  **Required professional action:** require characterization and negative-path tests before movement.
  **Route to:** `quality-test-gate`, `regression-testing`.
  **Evidence required:** current-behavior fixtures, risky branch map, command output, and assertion-quality note.
- **Signal:** A helper, file, class, module, `common`, `shared`, or `utils` target is introduced as part of refactoring.
  **Hidden risk:** ownership moves to a dumping ground, causing shared utility pollution, dependency-direction drift, or private-structure test coupling.
  **Required professional action:** inspect placement, reuse, and dependency direction before accepting the new shape.
  **Route to:** `implementation-structure-design`, `code-clarity-maintainability`.
  **Evidence required:** reuse search, owner boundary, rejected locations, dependency-direction proof, and public-behavior tests.
- **Signal:** Public API, schema, config key, event, metric, log field, generated client, or exported package surface changes during a refactor.
  **Hidden risk:** a breaking contract ships under a behavior-preserving label.
  **Required professional action:** stop pure refactor closure and route compatibility or consumer impact.
  **Route to:** `consumer-impact-analysis`, `data-api-contract-changer`.
  **Evidence required:** import/export or schema diff, consumer inventory, compatibility plan, migration/rollback note.
- **Signal:** Dead code, deprecated API, stale feature flag, fallback, compatibility branch, or obsolete abstraction is removed while reshaping code.
  **Hidden risk:** missing deletion safety, old/new branch tests, owner, expiry, or rollback path turns cleanup into unverified behavior loss.
  **Required professional action:** split cleanup governance from movement.
  **Route to:** `cleanup-deletion-governance`, `minimal-correct-implementation`.
  **Evidence required:** caller search, removal condition, owner/expiry, old/new behavior tests, and rollback limit.
- **Signal:** Project memory, prior incident notes, generated references, reflection/dynamic dispatch, or old validation says the refactor is safe without current-source confirmation.
  **Hidden risk:** stale context misses runtime callers or validation predates final movement.
  **Required professional action:** verify memory, graph, and validator freshness before handoff.
  **Route to:** `repository-graph-analysis`, `project-memory-governance`, `validation-broker`.
  **Evidence required:** searched graph map, accepted/rejected memory verdict, validator command output, report path, and remaining unknowns.
- **Signal:** Validation, formatter, build, code generation, or report commands run after structural movement but before final plan-vs-diff review.
  **Hidden risk:** execution order creates stale validation, generated artifact drift, or a tool-permission gap that makes the refactor look safer than it is.
  **Required professional action:** compare command order, changed paths, generated outputs, and validator freshness before closure.
  **Route to:** `validation-broker`, `agent-tool-permission-sandbox`.
  **Evidence required:** command order, changed-path validator map, exit code, generated artifact/report path, stale-validation decision, and rollback note.

# Risk Escalation Rules

Escalate when: the refactoring touches authorization, financial calculation, or data-integrity logic without existing characterization test coverage (requires test coverage before any change); the refactoring changes a public API, configuration key, database column name, event schema, or metric name (requires compatibility plan and consumer impact review); the refactoring is across a shared library used by multiple teams (requires cross-team communication and semantic versioning plan); the refactoring changes concurrency or locking behavior (requires concurrency review and load test); the refactoring is in a code path with a history of production incidents (requires incident history review and characterization tests before proceeding).

# Critical Details

- **Observable behavior is defined from the caller's perspective, not the implementer's.** Private field names, local variable names, and private method names are not observable. Return values, side effects, emitted events, database mutations, configuration file formats, and log output formats are observable. Before starting, write down the observable behavior boundary: "This refactoring preserves X and Y. It does NOT preserve Z (intentional change approved in [reference])."
- **Characterization tests are written to capture current behavior, not ideal behavior.** If the current code has a bug, the characterization test captures the buggy behavior. The goal is not to fix behavior — it is to detect if the structural change accidentally also changes behavior. Fix bugs in separate commits after the refactoring is complete and the structure is stable.
- **Authorization and financial code is the highest-risk category.** A sign flip in a conditional during an Extract Method, a wrong variable name during a Move Method, a missing `await` during an async extraction — any of these in authorization or financial code cause security incidents or financial loss. These sections require 100% branch coverage via characterization tests before any structural change, and a separate reviewer for the refactoring PR.
- **"Parallel change" (expand-contract) is the safe pattern for public contract refactoring.** (1) Expand: add the new interface alongside the old one — both exist, consumers use the old one. (2) Migrate: update all consumers to use the new interface. (3) Contract: remove the old interface. Each phase is a separate PR. This pattern allows rollback at each stage and avoids a big-bang migration that cannot be unwound.
- **Object, file, and module split or merge refactors follow the selected structure plan.** Use `implementation-structure-design` for file/object/function targets, small-file merge, and merge restraint; use `module-boundary-design` for module relationship type and dependency direction before moving code.
- **Compatibility branches must have an exit.** Deprecated APIs, feature flags, legacy switches, and fallback behavior need a named owner, expiry condition or date, removal trigger, and tests proving both old and new behavior until removal.

# Failure Modes

- **Null/empty semantic drift:** Refactoring changes a `null` return to an empty list in a shared utility; callers that used `result === null` to detect "not found" silently take the wrong branch.
- **Copied-condition inversion:** Extract Method moves code to a new private method but copies a conditional incorrectly; no test covers the negated branch, so a behavior change ships as structure.
- **Implicit public-contract rename:** A service is moved to a new package and the generated gRPC service name changes; existing clients fail because no compatibility plan or generated diff was reviewed.
- **Formatter-noise concealment:** A formatter run is mixed with logic movement, so reviewers miss the three semantic lines hidden inside hundreds of whitespace changes.
- **Calculation characterization gap:** `calculateTotal()` is refactored without characterization tests; rounding changes from `Math.round` to `Math.floor`, causing invoice reconciliation drift.
- **Authorization extraction regression:** `if (user.role !== 'guest')` becomes `isAuthorized(user)` and the extracted condition is inverted, creating an access outage or privilege error.
- **Responsibility-free split:** A large service is split into five files by method name, but every later change still edits all five because no owner, lifecycle, invariant, or collaborator boundary changed.
- **Unsafe file merge:** Small files are merged to reduce file count, hiding adapter side effects, value-object invariants, policy contracts, public behavior tests, and dependency direction.
- **Import/export drift:** A file split changes public exports and tests still pass only because callers use private internals, stale imports, or a generated barrel file that was not diffed.
- **Lost behavior test boundary:** A file merge removes a focused policy or adapter test boundary, so orchestration tests stay green while side-effect or failure semantics regress.
- **Permanent compatibility debt:** A deprecated API remains forever without owner, expiry, telemetry, or removal trigger, so new behavior keeps carrying legacy branches.
- **Feature-flag cleanup omission:** Feature flag cleanup is skipped after rollout, leaving old and new behavior active in the same function long after validation evidence is stale.
- **Stale execution closure:** Validation or generated-reference output predates the final move/merge/delete step, so handoff cites green evidence for code that was never exercised.

# Reference Loading Policy

Load only the reference needed for the active refactor decision:

- Load [references/checklist.md](references/checklist.md) when the refactor is high or critical risk, crosses files/modules/contracts, touches auth/financial/data-integrity/concurrency behavior, claims shared/common utility placement, removes cleanup debt, or needs the risk matrix, small-step mechanics, or anti-examples.
- Load [references/behavior-preservation-evidence.md](references/behavior-preservation-evidence.md) when behavior equivalence depends on repository graph freshness, project memory claims, generated references, dynamic callers, validation freshness, tool permission boundaries, or evidence limits.
- Load [references/split-merge-cleanup-patterns.md](references/split-merge-cleanup-patterns.md) when deciding file/object/module split, small-file merge, merge restraint, dead-code removal, deprecated API exit, feature-flag cleanup, compatibility branch expiry, or before/after complexity evidence.

Use [examples/example-output.md](examples/example-output.md) only when the plan shape is unclear. Do not load references for an isolated private rename with passing local tests and no observable behavior surface.

# Output Contract

Return a refactoring plan with:

- `target_smell` (what structural problem the refactoring addresses; named refactoring from Fowler catalog if applicable)
- `observable_behavior_boundary` (explicit list of outputs / side effects that must remain identical; any intentional non-behavioral changes listed separately with approval reference)
- `target_structure_decision` (where refactored functions belong; whether classes should split, collapse, or compose; whether files should split, merge, or stay separate with boundary; whether module boundaries change; which helpers stay private; which public APIs remain stable)
- `risk_classification` (Low / Medium / High / Critical per classification matrix)
- `characterization_test_plan` (per untested branch: test name, input fixture, expected output to capture; must be added before structural changes)
- `step_sequence` (ordered steps; each step is independently green; formatted as separate commits)
- `public_contract_impact` (any API shapes, config keys, DB columns, event schemas, metric names affected; compatibility plan if applicable)
- `formatting_separation` (confirm: formatter run committed separately before logic-movement steps)
- `review_slices` (PR boundaries: each PR is reviewable without context from other PRs; max ~300 lines of semantic diff)
- `rollback_plan` (which step can be reverted independently; git bisect feasibility)
- `verification_commands` (commands to confirm behavior preservation after each step)
- `mutation_testing_plan` (which tool; which target module; threshold for test suite adequacy)
- `excluded_changes` (changes explicitly out of scope that were identified during refactoring; tracked as separate work items)
- `object_split_refactor_plan` (large object or method-cluster split target, new owners, public behavior tests, and rejected splits)
- `file_split_refactor_plan` (large file split target, main responsibility per resulting file, private/public impact, and import changes)
- `file_merge_refactor_plan` (small or scattered file merge target, target owner, keep-separate alternatives, private/public impact, import/export before/after, and rollback step)
- `small_file_merge_plan` (merge candidates lacking independent owner/lifecycle/invariant/collaborator/public contract/side-effect/test/change-rhythm boundaries, target owner, tests, and rejected merges)
- `merge_restraint_decision` (small files kept separate because they protect adapter/client/gateway/repository/protocol/generated-code boundaries, value-object invariants, lifecycle/state machine, public behavior tests, current strategy/policy variants, dependency direction, side effects, or public contracts)
- `split_merge_behavior_preservation_evidence` (behavior tests before/after, characterization tests, contract tests, snapshots, import/export diff, public contract preserved, dependency direction preserved, and side-effect visibility preserved)
- `import_export_before_after` (imports and exports added, removed, renamed, or kept stable across the refactor)
- `public_contract_preserved` (API shapes, public exports, schemas, config keys, events, metrics, and caller-visible errors preserved or explicitly marked non-refactor)
- `dependency_direction_preserved` (layer/module import rules, cycles, adapter direction, and generated references remain valid)
- `behavior_test_before_after` (commands run before and after each split or merge step, including characterization tests for risky code)
- `module_split_refactor_plan` (module relationship type, dependency direction, public API impact, and migration steps)
- `cleanup_deprecation_plan` (dead code, deprecated API, legacy branch, or compatibility cleanup owner, expiry, and removal sequence)
- `feature_flag_removal_plan` (flag owner, rollout state, old/new behavior tests, removal trigger, and cleanup validation)
- `dead_code_removal_assessment` (callers searched, generated/runtime references checked, and deletion safety)
- `before_after_complexity_evidence` (cognitive complexity, branch count, collaborator count, dependency count, public API surface, directory density, or test clarity)
- `compatibility_branch_owner_and_expiry` (owner, expiry condition, follow-up artifact, and tests proving safe coexistence)
- `graph_memory_execution_validation` (repository graph freshness, accepted/rejected project-memory claims, changed-path validator map, validation freshness, and tool permission/sandbox record for refactor commands)

# Evidence Contract

A refactor is complete only when the output includes:

- **Behavior preservation evidence**: characterization tests, regression tests, contract tests, snapshots, or explicit no-test rationale.
- **Boundaries inspected**: callers, public APIs, imports, dependency direction, side effects, config, generated clients, reflection/dynamic dispatch, and tests.
- **Move/extract rationale**: why the new function, class, module, adapter, or value object owns the behavior.
- **Compatibility statement**: public contract, error semantics, data shape, ordering, timing, and side effects preserved or intentionally changed.
- **Dependency direction**: imports/layers remain valid or the boundary shift is explicitly routed to architecture review.
- **Split/merge preservation evidence**: import/export before/after, public contract preserved, dependency direction preserved, behavior test before/after, and side-effect boundary visibility for each file split or file merge.
- **Deletion path**: what old code becomes removable, when, and what proves removal is safe.
- **What refactor evidence proves**: behavior equivalence for covered public paths, import/export stability, dependency direction, cleanup safety, or complexity reduction for the inspected scope.
- **What refactor evidence does not prove**: untested consumers, dynamic reflection paths, runtime-only config, generated-client drift, performance side effects, or hidden integration dependencies.
- **Graph and memory freshness**: current source, generated artifacts, runtime registration, tests, and prior memory claims confirmed or rejected before closure.
- **Residual refactor risk**: uncovered behavior, stale validation, unsupported runtime edge, owner, and next gate.

# Quality Gate

The refactoring plan is complete only when:

1. Observable behavior boundary is explicitly defined — including any approved behavior changes.
2. Target structure decision states function placement, class split/collapse decisions, file split decisions, module boundary impact, private helpers, and preserved public APIs.
3. Risk classification is assigned; characterization tests planned or confirmed existing for High/Critical risk.
4. Step sequence is granular enough that each step passes the test suite independently.
5. No public contracts changed without a compatibility plan.
6. Formatting commits are separated from logic-movement commits.
7. Each review slice is ≤ 300 lines of semantic diff.
8. Rollback is possible for each step independently.
9. Verification commands are defined to confirm behavior preservation after all steps.
10. All behavior changes discovered during refactoring planning are extracted to separate work items.
11. Authorization, financial, and data-integrity code is covered by characterization tests before any structural change.
12. Large object, file, and module splits name the target owner, relationship type, and behavior-preservation tests.
13. File merge and file split steps preserve observable behavior, public contracts, dependency direction, side-effect boundaries, and behavior tests before/after.
14. High-risk file merge or split refactors add or confirm characterization tests before moving code.
15. Each merge or split step is independently reviewable, revertable, and testable.
16. File movement, merge, split, import/export cleanup, and behavior change are not mixed in the same step.
17. Dead code, deprecated APIs, feature flags, and compatibility branches have removal owner, expiry, and cleanup validation.
18. Before/after complexity evidence is recorded or the lack of reduction is justified.
19. Repository graph, project memory, generated references, reflection/dynamic dispatch, and validation freshness are reconciled before handoff.
20. Tool permission/sandbox evidence exists for broad move, rename, format, test, build, generated-artifact, or deletion commands.

# Used By

- ai-code-review-refactor
- architecture-impact-reviewer

# Handoff

Hand off to `code-review` for diff assessment against the step sequence plan; `test-strategy` for behavior protection on code not yet covered by tests; `module-boundary-design` for target structure design when boundaries are unclear; `profiling` when optimization is needed after refactoring is complete and baseline is re-measured.

# Completion Criteria

The capability is complete when **every structural change is independently reviewable, behavior preservation is proven by characterization or public behavior tests passing before and after each step, file split and file merge plans preserve import/export surfaces, public contracts, dependency direction, and side-effect boundaries, all public contract impacts are resolved, and every behavior change discovered during the refactoring is tracked as an explicit separate work item**.
