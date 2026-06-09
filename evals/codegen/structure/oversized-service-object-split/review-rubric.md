# Review Rubric

## Passing Standard

The solution passes when it refuses to grow the oversized service, creates cohesive owners for cancellation and refund decisions, keeps side effects in orchestration/adapters, and proves behavior through public tests.

## Scoring

- 30 percent structure: one main responsibility per file, justified object split, and no helper bag.
- 25 percent clarity: readable main flow, named conditions, structured signatures, and no weak type bags.
- 25 percent tests: public behavior tests for existing and new cancellation outcomes.
- 10 percent refactor safety: behavior-preserving sequence and before/after complexity evidence.
- 10 percent local convention: existing order vocabulary, placement, and test conventions followed.

## Automatic Failure Conditions

- Adds premium/disputed branches directly to a large `OrderService` method.
- Moves order business logic to shared/common/utils.
- Introduces speculative factory, strategy, or interface for one implementation.
- Tests private helpers instead of public order behavior.

## Reviewer Notes

Reward boring, explicit ownership over clever abstraction. Penalize changes that make the call path harder to read even if the code is split across more files.
