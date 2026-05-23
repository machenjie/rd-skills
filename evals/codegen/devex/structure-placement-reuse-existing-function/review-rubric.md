# Review Rubric

## Passing Standard

The solution must reuse existing helpers where semantics match, keep business
logic in owning modules, and document placement choices before accepting new
code. A reviewer should be able to trace why no duplicate utility was needed.

## Scoring

- 30 percent reuse correctness for `normalizeEmail()` and `validateTenantAccess()`.
- 25 percent implementation structure for placement rationale and rejected alternatives.
- 20 percent test quality for normalized lookup and authorization denial.
- 15 percent dependency direction and minimal exports.
- 10 percent maintainability for naming and avoiding shared utility pollution.

## Automatic Failure Conditions

- Reimplementing normalizeEmail locally instead of reusing the existing helper.
- Adding tenant or invitation business validation under shared utils or common utils.
- Creating a public export only used by one module.
- Tests only assert private helper calls and not public invitation behavior.

## Reviewer Notes

Strong answers search nearby and project-wide code before editing, compose the
existing tenant policy, and keep tests at the invitation behavior boundary.
