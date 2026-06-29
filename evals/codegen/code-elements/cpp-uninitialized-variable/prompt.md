# Benchmark Prompt

## Task

Fix a C++ uninitialized variable bug in a status calculation.

## Context

The starter repo has a local variable that is assigned only in some branches and
then used in a return expression. The fix must be local and idiomatic.

## Requirements

- Ensure every read is dominated by initialization.
- Preserve existing status behavior for all branches.
- Add tests for every branch, including the previously uninitialized path.
- Include a Code Element Professionalism Review and C++ idiom note.

## Constraints

- Do not silence compiler warnings without fixing the cause.
- Do not introduce global state or a new status helper file.
- Do not change public enum values or API names.

## Deliverables

- Updated C++ implementation.
- Branch regression tests.
- Validation evidence with compiler or test output.

## Completion Evidence

- Tests cover every branch that reads the variable.
- Handoff states why initialization is now complete.

