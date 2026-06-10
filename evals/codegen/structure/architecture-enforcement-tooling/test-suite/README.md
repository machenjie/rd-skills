# Test Suite

## Required Checks

- Architecture rule documentation only and manual code review only are rejected.
- CI command covers import boundary, cycle, public/private export, and forbidden dependency checks as applicable.
- Generated code exception policy is tested or documented.
- Failure examples show what a contributor sees when a rule fails.

## Fixtures

Architecture fixtures belong to the module-boundary test boundary and must name the rule, violating import, expected tool, and exception status.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Domain cannot import API layer.
- UI cannot import persistence layer directly.
- Cycle detection catches a representative module cycle.
- Generated clients are excluded only by explicit path rule.
