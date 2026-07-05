# Review Rubric

## Passing Standard

The solution passes when it implements the requested label behavior through the
lowest valid ladder level and rejects added structure that has no current force.

## Scoring

- 35 percent Minimal Correctness Decision quality.
- 25 percent reuse and placement evidence.
- 20 percent rejection of speculative service, factory, registry, config, or shared utility surface.
- 15 percent public behavior test coverage.
- 5 percent concise handoff with residual risk.

## Automatic Failure Conditions

- Service or factory is introduced for one order label rule.
- Shared utils receive order business terms without ownership evidence.
- Config switch, registry, or interface is added without current consumers.
- Tests target only private helpers or are not runnable.
- "Fewest files" is used as the sole placement rationale.

## Reviewer Notes

Strong answers are small because the current requirement is small, not because
they ignore ownership, testing, or handoff obligations.
