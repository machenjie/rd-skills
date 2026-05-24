# Review Rubric

## Passing Standard

The solution must demonstrate that existing formatter logic was searched and
reused or deliberately rejected before any helper is added. The final placement
must keep order business behavior in the owning module and include execution
evidence for the tests or validators that prove the change.

## Scoring

- 30 percent reuse search quality and named candidates.
- 25 percent placement rationale and shared utility avoidance.
- 20 percent test coverage through public order behavior.
- 15 percent execution evidence and residual-risk clarity.
- 10 percent maintainability and minimal public surface.

## Automatic Failure Conditions

- Adds order business logic to shared/common/utils.
- Duplicates an existing formatter without a documented reason.
- Creates a public export only used by one module.
- Reports the change complete without concrete validation evidence.

## Reviewer Notes

Strong answers start with local and project-wide search, name the existing
helpers inspected, and keep the change small. The review should reject clever
new abstractions when existing owner modules already provide the concept.