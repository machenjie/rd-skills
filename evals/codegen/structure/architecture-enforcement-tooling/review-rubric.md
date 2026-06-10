# Review Rubric

## Passing Standard

The solution passes when architecture rules become runnable checks, CI integration is explicit, generated exceptions are scoped, and contributors can understand failures.

## Scoring

- 30 percent rule coverage: import, cycle, export, forbidden dependency, lint, type-check, dead code, and complexity coverage is appropriate.
- 25 percent tool fit: selected tool matches language, framework, and local build system.
- 20 percent CI integration: command, failure behavior, and ownership are clear.
- 15 percent migration and exceptions: generated code and legacy violations have bounded handling.
- 10 percent usability: failure examples and contributor guidance are concrete.

## Automatic Failure Conditions

- Architecture rules remain documentation only with no CI gate.
- Import boundary rules lack failure examples or runnable command.
- Generated code is blocked without exception policy.
- Enforcement depends only on manual code review.

## Reviewer Notes

Prefer smallest sufficient tooling already present in the stack. Penalize broad new dependencies when an existing linter, import checker, or type checker can enforce the rule.
