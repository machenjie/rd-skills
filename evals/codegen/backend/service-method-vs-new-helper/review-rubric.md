# Review Rubric

## Passing Standard

The implementation must keep cancellation deadline logic in the order domain or
service ownership path, reuse existing policy structure, and prove behavior
through the public cancellation workflow.

## Scoring

- 30 percent business rule ownership and service/policy reuse.
- 25 percent deadline correctness for before, exact, and after boundary cases.
- 20 percent test quality through public behavior.
- 15 percent implementation structure plan and rejected alternatives.
- 10 percent dependency direction and minimal public API surface.

## Automatic Failure Conditions

- Adding validateCancellationDeadline to shared utils or common utils.
- Bypassing OrderService transaction or authorization flow.
- Creating a stateless class only to group helper functions.
- Tests cover only private helpers and not public cancellation behavior.

## Reviewer Notes

Strong answers treat date comparison as technical detail and cancellation
eligibility as order policy. Keep new helper scope private unless there is a
current multi-module contract.
