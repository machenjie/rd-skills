# Benchmark Prompt

## Task

Fix a null-profile bug only after scanning for the same dereference pattern in
the rest of the codebase.

## Context

`GET /users/{id}/profile` fails when a user has no profile because one controller
dereferences `profile.name`. Similar profile dereferences may exist in other
controllers, services, or serializers. A local one-line null check is not enough
unless the rest of the pattern is scanned and the local-only scope is justified.

## Requirements

- Identify the defect pattern signature before editing.
- Search relevant backend modules for the same dereference or assumption.
- Fix every occurrence that shares the same user-visible defect, or document why
  specific occurrences are intentionally out of scope.
- Add regression tests for the reported endpoint and any covered sibling path.
- Include a same-pattern scan record in the Execution Discipline Report.

## Constraints

- Do not add a broad defensive wrapper that hides authorization or data-quality
  errors.
- Do not change unrelated user serialization behavior without impact analysis.
- Do not claim the bug is fixed after changing only the reported line unless the
  scan supports that local-only decision.

## Deliverables

- Minimal bug fix covering the scanned impact scope.
- Regression tests for missing-profile behavior.
- Same-pattern scan record with pattern, scope, matches, decision, validation,
  residual risk, and handoff boundary.

## Completion Evidence

- Test output proving the reported bug no longer occurs.
- Search output or inspected-file list for the same pattern.
- Rationale for all matching occurrences covered or excluded.