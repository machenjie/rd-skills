# Benchmark Prompt

## Task

Fix an unintended C++ switch fallthrough in status handling.

## Context

The starter repo has a `switch` where `Suspended` falls through into `Active`
handling with no explicit marker.

## Requirements

- Make each case behavior explicit.
- Add branch tests for suspended, active, and unknown statuses.
- Preserve public enum and return values unless a behavior change is approved.
- Include code-element and C++ idiom evidence.

## Constraints

- Do not silence fallthrough warnings without clarifying behavior.
- Do not rewrite the status system.
- Do not change public enum names.

## Deliverables

- Updated C++ switch handling.
- Regression tests for each case.
- Handoff with fallthrough decision and validation evidence.

## Completion Evidence

- Test output for suspended and active branches.
- Review note saying whether fallthrough is removed or explicit.

