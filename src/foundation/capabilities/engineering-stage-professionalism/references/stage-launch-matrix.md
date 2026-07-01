# Stage Launch Matrix

Use this reference when the `SKILL.md` body is not enough to decide launch set, evidence obligation, legal transition, skipped-heavy rationale, or graph/memory/execution freshness.

## Launch Matrix

| Stage | Launch focus | Skip by default |
| --- | --- | --- |
| requirement-intake | `requirement-clarification`, `requirement-structuring`, `non-goal-boundary-definition`, `acceptance-standard-definition`, `scenario-decomposition` | coding, language, testing, refactoring, release |
| architecture-design | `architecture-style-selection`, `module-boundary-design`, `layered-architecture-design`, `architecture-tradeoff-analysis`, `extensibility-design`, `solution-optimality-evaluation` | language idiom, coding, test authoring |
| implementation-planning | `repository-context-map`, `implementation-structure-design`, `module-boundary-design`, `code-clarity-maintainability`, `language-idiom-enforcement`; add `senior-programming-judgment-core` when object, state, rule, side-effect, failure, validation, observability, or residual-risk evidence is material | full architecture review, release, deep performance profiling |
| coding | matching language professional usage capability, `language-idiom-enforcement`, `input-validation`, `logging-error-handling`; add `senior-programming-judgment-core` for non-trivial behavior, state, rule, invariant, failure, side-effect, validation, or observability changes | architecture deep review, release, full regression suite design |
| debugging-diagnosis | `failure-diagnosis`, `agent-execution-discipline`, `observability` | refactoring, new design |
| bug-fix | `agent-execution-discipline`, `regression-testing`, `code-review`; add `minimal-correct-implementation` for minimal fix, delete/shrink, dependency, abstraction, wrapper-only delegation, shortcut, or overengineering signals | architecture redesign |
| code-review | `code-review`, `plan-execution-consistency`, `implementation-structure-design`, `code-clarity-maintainability`, `language-idiom-enforcement`; add `ai-code-review-refactor` for generated code | release, deployment, infrastructure |
| refactoring | `refactoring`, `implementation-structure-design`, `code-clarity-maintainability`, `code-review`, `regression-testing` | feature design, release |
| testing | `test-strategy`, `plan-execution-consistency`, `language-testing-strategy`, `test-data-management`, matching test capability | architecture redesign, new feature coding |
| release-delivery | `ci-cd`, `release-rollback`, `containerization`, `kubernetes-gateway`, `observability`, `backup-recovery` | language deep checks, coding |
| documentation-handoff | `agent-workflow-state-machine`, `plan-execution-consistency`, `documentation-generation`, `agent-execution-discipline` | coding capabilities |
| skill-authoring | `repository-context-map`, `skill-authoring-expert`, `skill-efficacy-benchmark`, `documentation-generation`, `agent-execution-discipline`, `plan-execution-consistency`; add `senior-programming-judgment-core` for hook, routing, registry, schema, eval, benchmark, or closure behavior changes | product coding, language runtime, release |

## Evidence By Stage

| Stage | Professional evidence required |
| --- | --- |
| requirement-intake | current behavior, desired behavior, non-goals, constraints, assumptions, open questions, and testable completion signal |
| architecture-design | affected boundaries, dependency direction, ownership, simpler alternative, tradeoff, and rollback implication |
| implementation-planning | inspected target-project boundaries, reuse ladder, placement rationale, touched files, validation commands, senior programming judgment record or allowed skip reason, and split/sequence decision |
| coding | inspected local convention, selected capabilities, changed boundary, TDD or validation signal, tests or validators run, senior programming judgment evidence when behavior is non-trivial, and residual risk |
| debugging-diagnosis | symptom, hypothesis tested, method, verified cause, counter-evidence, and no same-path third retry |
| bug-fix | verified cause, same-pattern scan, regression proof, old behavior preservation, and local/broad fix rationale |
| code-review | independent review owner, severity-classified findings, boundary inspected, missing evidence, behavior-change risk, required fix owner, and re-review result when repaired |
| refactoring | before/after behavior preservation, affected callers, deletion path, placement decision, and regression evidence |
| testing | risk-based test level, fixture/data owner, what the test proves, what it does not prove, and flaky-risk note |
| release-delivery | rollout plan, rollback path, config/migration compatibility, monitoring signal, and owner acceptance |
| documentation-handoff | affected artifacts, no-change rationales, validation/link checks, residual doc risk, and owner |
| skill-authoring | source body/reference boundary, registry impact, senior programming judgment record when runtime or evaluation behavior changes, validators/evals run, and no runtime architecture drift |

## Transition Rules

- Move from diagnosis to bug-fix only after a verified cause exists or the next action is reversible instrumentation.
- Move from requirement-intake to implementation-planning only after blocking questions are resolved or assumptions and residual risk are explicit.
- Move from implementation-planning to coding only after target evidence, reuse, placement, validation, and skipped heavy capabilities are named.
- Move from coding to testing only after changed behavior and residual risk are explicit; select tests by risk, not habit.
- Move from coding to code-review only with a reviewer different from the action owner.
- Move from code-review to repair, refactoring, or bug-fix only when findings name repair owner and required re-review.
- Move from testing to release-delivery only when test evidence states what it proves, what it does not prove, and remaining release risk.
- Move from release-delivery to documentation-handoff when rollout, rollback, migration, config, or operational behavior changes reader obligations.

## Stage-Specific Hidden Risks

- **Implementation-planning:** missing reuse/placement evidence creates helpers, public exports, or directories before ownership is known.
- **Implementation-planning:** missing senior programming judgment lets code shape proceed without source-backed facts, object/state/rule mapping, side effects, failure contract, validation map, observability decision, or residual risk owner.
- **Coding:** local code success can hide contract, tenant, transaction, retry, or release-skew risks selected by the active professional skill.
- **Debugging-diagnosis:** symptom patching and same-path retry can produce a plausible diff without a verified cause.
- **Bug-fix:** one local fix can leave the same defect pattern in sibling modules unless the same-pattern scan is recorded.
- **Code-review:** review can drift into implementation or release planning before severity-classified findings and evidence gaps are named.
- **Testing:** adding tests by habit can miss the risk that matters, such as contract compatibility, regression proof, fixture ownership, or negative cases.
- **Release-delivery:** deploy rollback can be invalid when migrations, feature flags, old/new versions, or config defaults changed state.

## Graph, Memory, And Execution Coupling

- Treat repository graph and project memory as selectors until current source confirms them.
- If compaction or prior trajectory says a stage is done, compare with current files, reports, validation order, and route/stage manifests.
- Validation evidence is fresh only when it ran after final material source, registry, reference, report, generated, package, or install-output edits.
- Repair after review needs a repair ledger and targeted re-review before the stage can advance.
- If stage selection changes, discard out-of-stage launch context and hand off the produced evidence to the next stage.
