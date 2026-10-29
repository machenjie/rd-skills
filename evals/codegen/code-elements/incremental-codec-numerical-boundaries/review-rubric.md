# Review Rubric

## Passing Standard

The adapter returns correct frames, bytes, and numerical outcomes for the specified contract. Assertions exercise functions rather than source wording.

## Scoring

Assess framing and EOF correctness, bounded resource use, independent numerical invariants, and separation of numerical residual from model applicability and endpoint agreement. Credit analytic references, replayable failures, and clear proof limits.

## Automatic Failure Conditions

Accepting truncated EOF as a complete stream fails. Replaying an acknowledged write prefix, treating iteration exhaustion as convergence, or accepting zero residual for an unsupported rod regime or wrong endpoints also fails.

## Reviewer Notes

Finite deterministic examples do not prove arbitrary encodings, real transport behavior, mixed-precision kernels, actual scientific solver correctness, or physical suitability beyond the declared source-free rod model.
