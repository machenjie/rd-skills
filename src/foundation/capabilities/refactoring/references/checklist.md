# Refactoring Checklist

- State the structural problem and target improvement.
- Define observable behavior that must not change.
- Identify public contracts, schema, config, metrics, and integration boundaries.
- Add characterization tests for risky or poorly understood behavior.
- Split movement into small reviewable steps.
- Avoid mixing formatting churn with logic movement.
- Verify behavior after risky steps.
- Record rollback notes and any explicit behavior-change exclusions.

## Risk Classification

| Risk Level | Code Characteristics | Required Preparation | Step Size |
| --- | --- | --- | --- |
| Low | Covered by tests; no external contracts; private/internal scope. | Verify the relevant suite passes first. | Individual commit per transformation. |
| Medium | Partially covered; touches internal API or shared utility. | Add characterization tests for uncovered branches. | Separate commit per refactoring type. |
| High | Untested or complex; auth, money, data integrity, public contract, or concurrency. | Full characterization suite and reviewer plan before movement. | One mechanical change per PR. |
| Critical | Shared library, public API, schema-adjacent path, runtime registration, or cross-team consumer. | Compatibility plan, consumer impact review, deprecation/removal strategy. | Separate PR per contract boundary. |

## Step Discipline

1. Define the observable behavior boundary: outputs, DB mutations, events, side effects, ordering, errors, public exports, logs, and metrics that must remain identical.
2. Define the target structure decision: owners, private/public helpers, split/merge targets, module boundaries, and rejected shared/common/utils placement.
3. Check existing coverage. Add characterization tests before touching risky, poorly understood, or uncovered branches.
4. Sequence independently green steps: rename, extract, move, inline, split, merge, import/export cleanup, deletion, and behavior change each stand alone.
5. Separate formatting from logic movement.
6. After each step, inspect the diff, run mapped validators, and stop on failure rather than continuing a broken refactor.
7. After all steps, record before/after complexity evidence such as cognitive complexity, branch count, collaborator count, dependency count, public API surface, directory density, or test clarity.

## Anti-Examples

| Anti-pattern | Problem | Corrected approach |
| --- | --- | --- |
| Refactor PR includes renames plus a changed return type. | Behavior change is hidden inside movement. | Separate rename-only refactor from explicit behavior-change work. |
| "I'll add tests after the refactor." | No safety net detects accidental behavior drift. | Add characterization tests before risky movement. |
| Extract class and change logic in the same commit. | Reviewer cannot distinguish extraction from behavior change. | Extract first with tests green; change logic separately. |
| Rename a database column while refactoring service code. | Schema migration and structural movement have different rollback paths. | Use expand/contract migration first, then refactor service code, then cleanup. |
| Large whitespace reformat mixed with 10 semantic lines. | Review signal is hidden in noise. | Commit formatter-only changes separately. |
| Optimize a hot path "while refactoring." | Optimization needs measurement and can change behavior. | Refactor first; optimize later with baseline and after measurement. |

## Characterization Test Pattern

Use characterization tests to capture current behavior, not ideal behavior. If the current behavior is wrong, capture it first, refactor safely, then fix the bug in separate behavior-change work.

```javascript
test("characterizes current invoice total behavior", () => {
  const result = calculateTotal(fixtureOrderWithDiscount);
  expect(result).toBe(127.50);
});
```
