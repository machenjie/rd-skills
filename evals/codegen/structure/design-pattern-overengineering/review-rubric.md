# Review Rubric

## Passing Standard

The solution passes when it selects direct code or a module-local helper for
one current rule and explicitly rejects unnecessary pattern machinery.

## Scoring

- 35 percent Design Pattern Decision Record quality.
- 25 percent rejection of speculative strategy, factory, interface, and base class.
- 20 percent preservation of object, method, module, and file granularity.
- 15 percent public behavior test coverage.
- 5 percent naming and local convention fit.

## Automatic Failure Conditions

- Strategy with one implementation is introduced.
- Factory hiding simple constructor or direct function call is introduced.
- Abstract base class for reuse is introduced.
- Public interface with no current consumer is exported.
- File split exists only to reduce line count or test a private helper.

## Reviewer Notes

Strong answers keep the code boring and document the pattern rejection as a
professional decision, not as an absence of design.
