---
name: refactoring
description: Guides behavior-preserving code reshaping with characterization tests for risky changes and explicit handling of boundaries, contracts, and rollback.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "79"
changeforge_version: 0.1.0
---

# Mission

**Improve code structure while provably preserving observable behavior** — using characterization tests before reshaping risky code, keeping steps small enough to review and revert independently, protecting public contracts and persistence boundaries, and making every behavior change an explicit, separately approved decision rather than an inadvertent side effect of structural movement.

# When To Use

Use this capability when: simplifying a method, class, or module that has accumulated mixed responsibilities over time; extracting a reusable abstraction from duplicated logic; renaming concepts to align with the current domain model; reducing coupling between modules to enable independent testing or deployment; removing dead code or obsolete abstractions; preparing a codebase section for a future behavior change by isolating dependencies first; or when a code review flags "this is hard to read" or "this is fragile" without requiring behavior change.

# Do Not Use When

Do not use this capability to: change observable behavior and label it as a refactor ("I just cleaned it up" while changing return values, validation logic, or error handling); rewrite stable, correct, well-tested code in a different style or paradigm purely out of preference; churn public API contracts, database column names, configuration keys, or metric names without a compatibility plan and consumer impact review; or optimize for performance (use `profiling` to identify the bottleneck first; optimization changes are not structure-only — they require before/after measurement).

# Non-Negotiable Rules

- **Refactoring must preserve observable behavior unless a behavior change is explicitly approved, documented, and reviewed as a separate step.** "Observable behavior" means: the outputs produced for the same inputs (function return values, API response shapes, database mutations, emitted events, side effects visible to callers). Internal representation changes (private field names, local variable renaming, private method extraction) are not observable. Changing a `null` return to an empty array is observable — it is a behavior change, not a refactor.
- **Risky refactoring requires characterization tests before structural changes begin.** "Risky" means: the code under change is not covered by tests; the code has complex control flow, concurrency, or state management; the code touches authorization, financial calculations, or data integrity; or the code interacts with external systems. Characterization tests (Michael Feathers "Working Effectively with Legacy Code") — tests that capture current behavior, even if that behavior is imperfect — are the safety net that makes structural changes reviewable.
- **Each refactoring step must be reviewable and revertable independently.** Large refactors committed in a single 2,000-line diff are not reviewable — reviewers cannot distinguish behavior-preserving movement from accidental change. Rule: each step must be a logical unit that passes all tests independently. Rename and move classes in separate commits from changing their logic. Extraction and injection in separate commits. If git bisect cannot identify which step introduced a regression, the steps were too large.
- **Public contracts must not change without a compatibility plan.** Public contracts include: API endpoint request/response shapes, gRPC/OpenAPI/AsyncAPI schemas, configuration keys and environment variable names, database column names and table structures, event/message payload schemas, public library function signatures, metric and log field names. Changing any of these is not a refactor — it is a breaking change requiring versioning, migration, or consumer coordination.
- **Formatting changes must not be mixed with semantic changes in the same commit.** A commit that reformats 400 lines of code while also changing 3 lines of logic makes it impossible to review the logical change. Rule: formatting-only commits are separate from logic-movement commits. Use automated formatters (prettier, black, gofmt) to separate formatting from semantic changes completely.
- **Refactoring must not be used to smuggle performance optimizations without measurement.** "I refactored this to be more efficient" while changing an O(n²) algorithm to O(n log n) is a behavior-change-adjacent optimization, not a pure structural change. Optimization requires baseline measurement and validation. Refactor and optimize in separate changes.
- **Authorization, financial calculations, and data integrity logic must have behavior-equivalence tests before any structural change.** These are the highest-risk code categories. A refactoring mistake in an authorization check can introduce a privilege escalation. A refactoring mistake in a financial calculation can produce incorrect totals. Extract characterization tests that cover all branches before touching these areas.

# Industry Benchmarks

Anchor against: **Martin Fowler "Refactoring: Improving the Design of Existing Code" (2nd ed., 2018)** — catalog of named refactorings (Extract Method, Extract Class, Move Method, Replace Conditional with Polymorphism, Inline Method); each refactoring has a motivation, mechanics, and before/after example. **Michael Feathers "Working Effectively with Legacy Code" (2004)** — characterization testing; seam model (finding seam points to break dependencies for testing); techniques for getting untestable code under test. **Kent Beck "Small Steps" principle** — always keep the system in a working state; red/green/refactor cycle; commit after every green bar. **Semantic Versioning (semver.org)** — any change to a public API that is not backward-compatible is a MAJOR version change; public contract awareness is prerequisite for refactoring shared libraries. **ArchUnit / Dependency Cruiser** — automated structural rule enforcement; detects if refactoring violates intended dependency direction (e.g., domain layer importing from infrastructure layer). **git bisect** — binary search through commits to find the regression; only works if each commit independently passes tests. **Mutation testing (Stryker, PITest)** — reveals characterization tests that are too weak to catch behavior changes during refactoring. **SonarQube cognitive complexity** — quantifies whether a refactoring actually reduced cognitive load (before/after cognitive complexity score).

### Refactoring Risk Classification

| Risk Level | Code Characteristics | Required Preparation | Step Size |
| --- | --- | --- | --- |
| Low | Covered by tests; no external contracts; private/internal scope | Verify test suite passes; proceed | Individual commit per transformation |
| Medium | Partially covered; touches internal API or shared utility | Add characterization tests for uncovered branches first | Separate commit per refactoring type |
| High | Untested or complex; authorization/financial/data integrity logic; public contract | Full characterization test suite first; review plan with team | One mechanical change per PR |
| Critical | Shared library; public API; database schema-adjacent; concurrency | Compatibility plan; consumer impact review; deprecation strategy | Separate PR per contract boundary |

### Refactoring Step Discipline

```
Before starting any refactoring:

1. Define Observable Behavior Boundary
   What outputs (return values, DB mutations, events, side effects) must remain identical?
   Document: "This refactoring preserves X; does NOT preserve Y (intentional change)"

2. Define Target Structure Decision
   Which functions should stay private? Which classes should be split, collapsed, or composed? Which files should own the extracted behavior? Which module boundaries or public APIs must stay unchanged?
   Reject new shared/common/utils placement unless the extracted code is a pure technical utility with no business terminology.

3. Check Test Coverage
   Run coverage report on the target code.
   If coverage < acceptable threshold → write characterization tests first.
   Characterization test pattern:
     test("characterizes current behavior of OrderService.calculateTotal", () => {
       const result = calculateTotal(fixture_order_with_discount);
       expect(result).toBe(127.50); // captures current behavior; fix intentionally later
     });

4. Plan Step Sequence (each step independently passing)
   Step 1: Rename internal variables (no logic change)
   Step 2: Extract private helper method (no logic change)
   Step 3: Move method to correct class (no logic change)
   Step 4: [Optional] Replace conditional with polymorphism
   Each step: commit → run full test suite → verify green

5. Separate Formatting
   Run formatter BEFORE starting refactoring on files you will touch.
   Formatting commit is separate from any logic movement.

6. After Each Step
   git diff --stat → confirm line count is reasonable
   Run all tests (unit + integration for touched boundaries)
   If any test fails → revert the step; do not proceed with failing tests

7. After All Steps
   Run mutation testing on characterized code → verify tests actually protect behavior
   Measure before/after complexity score (cognitive complexity) → confirm improvement
```

### Anti-examples

| Anti-pattern | Problem | Fix |
| --- | --- | --- |
| Refactor PR includes: 3 renamed methods + 1 changed return type | Return type change is a behavior change disguised as structural movement; reviewer misses it | Separate commit / PR: rename-only PR followed by explicit behavior-change PR with changelog |
| "I'll add tests after the refactor" | No safety net during refactoring; one mechanical slip changes behavior silently | Write characterization tests before structural changes on risky code |
| Extract class + change logic in same commit | Impossible to review: is the behavior change from the extraction or the logic change? | Extract class first (passes tests); change logic in separate commit (passes tests) |
| Rename `user_id` column in migration + refactor service layer in same PR | Schema migration is a breaking change; conflated with structural refactoring; rollback is complex | Separate: (1) migration + backward-compatible app code; (2) refactor service layer; (3) cleanup old compat code |
| 1,800-line refactoring PR with comment "just cleanup" | Reviewer cannot verify behavior preservation; rubber-stamp review; regression introduced | Max ~300 lines per refactoring PR; each commit is independently green |
| Optimize hot path "while I was in there refactoring" | Optimization requires before/after profiling measurement; mixed with structural change; cannot validate improvement | Separate PRs: (1) refactoring; (2) optimization with baseline + after measurement |

# Selection Rules

Select this capability when **structural improvement is the primary goal and behavior must be preserved**. Route elsewhere when: `code-review` is primary (evaluating an existing diff for correctness and review feedback); `module-boundary-design` is primary (deciding what the target architecture should be — use that first, then refactor toward it); `test-strategy` is primary (defining what tests are needed for new functionality — not preserving existing behavior); `profiling` is primary (measuring and reducing performance bottleneck — optimize after refactoring, not during); `api-contract-design` is primary (changing a public API contract — that is a breaking change, not a refactoring).

# Risk Escalation Rules

Escalate when: the refactoring touches authorization, financial calculation, or data-integrity logic without existing characterization test coverage (requires test coverage before any change); the refactoring changes a public API, configuration key, database column name, event schema, or metric name (requires compatibility plan and consumer impact review); the refactoring is across a shared library used by multiple teams (requires cross-team communication and semantic versioning plan); the refactoring changes concurrency or locking behavior (requires concurrency review and load test); the refactoring is in a code path with a history of production incidents (requires incident history review and characterization tests before proceeding).

# Critical Details

- **Observable behavior is defined from the caller's perspective, not the implementer's.** Private field names, local variable names, and private method names are not observable. Return values, side effects, emitted events, database mutations, configuration file formats, and log output formats are observable. Before starting, write down the observable behavior boundary: "This refactoring preserves X and Y. It does NOT preserve Z (intentional change approved in [reference])."
- **Characterization tests are written to capture current behavior, not ideal behavior.** If the current code has a bug, the characterization test captures the buggy behavior. The goal is not to fix behavior — it is to detect if the structural change accidentally also changes behavior. Fix bugs in separate commits after the refactoring is complete and the structure is stable.
- **Authorization and financial code is the highest-risk category.** A sign flip in a conditional during an Extract Method, a wrong variable name during a Move Method, a missing `await` during an async extraction — any of these in authorization or financial code cause security incidents or financial loss. These sections require 100% branch coverage via characterization tests before any structural change, and a separate reviewer for the refactoring PR.
- **"Parallel change" (expand-contract) is the safe pattern for public contract refactoring.** (1) Expand: add the new interface alongside the old one — both exist, consumers use the old one. (2) Migrate: update all consumers to use the new interface. (3) Contract: remove the old interface. Each phase is a separate PR. This pattern allows rollback at each stage and avoids a big-bang migration that cannot be unwound.

# Failure Modes

- Refactoring changes a `null` return to an empty list in a shared utility — three callers check `result === null` to detect "not found"; all three now receive an empty list and treat it as "found empty" — silent behavior change; discovered weeks later in production data inconsistency.
- Extract Method refactoring moves code to a new private method but copies a conditional incorrectly — the condition is negated; no test covers the negated branch; behavior change shipped to production.
- Service renamed and moved to a new package — gRPC service name changes implicitly — existing clients fail with "service not found"; no compatibility plan; 2-hour production outage.
- Formatter run mixed with logic changes in same commit — code reviewer sees 800-line diff of whitespace changes plus 10 lines of logic; misses the logic change in the noise.
- `calculateTotal()` refactored without characterization tests — floating-point rounding behavior changes from `Math.round` to `Math.floor` during extraction — invoice totals off by $0.01; discovered in monthly reconciliation.
- Authorization check refactored: `if (user.role !== 'guest')` extracted to `isAuthorized(user)` — during extraction, condition inverted: `if (user.role === 'guest')` — all non-guest users lose access; prod incident.

# Output Contract

Return a refactoring plan with:

- `target_smell` (what structural problem the refactoring addresses; named refactoring from Fowler catalog if applicable)
- `observable_behavior_boundary` (explicit list of outputs / side effects that must remain identical; any intentional non-behavioral changes listed separately with approval reference)
- `target_structure_decision` (where refactored functions belong; whether classes should split, collapse, or compose; whether files should split; whether module boundaries change; which helpers stay private; which public APIs remain stable)
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

# Used By

- ai-code-review-refactor
- architecture-impact-reviewer

# Handoff

Hand off to `code-review` for diff assessment against the step sequence plan; `test-strategy` for behavior protection on code not yet covered by tests; `module-boundary-design` for target structure design when boundaries are unclear; `profiling` when optimization is needed after refactoring is complete and baseline is re-measured.

# Completion Criteria

The capability is complete when **every structural change is independently reviewable, behavior preservation is proven by characterization tests passing before and after each step, all public contract impacts are resolved, and every behavior change discovered during the refactoring is tracked as an explicit separate work item**.
