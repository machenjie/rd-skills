# Review Rubric

## Passing Standard

The adapter returns correct frames, bytes, and numerical outcomes for the specified contract. Assertions exercise functions rather than source wording.

## Scoring

Assess framing and EOF correctness, bounded resource use, and independent numerical invariants. Credit replayable failures and clear proof limits.

## Automatic Failure Conditions

Accepting truncated EOF as a complete stream fails. Replaying an acknowledged write prefix or treating iteration exhaustion as convergence also fails.

## Reviewer Notes

Finite deterministic examples do not prove arbitrary encodings, real transport behavior, mixed-precision kernels, or production numerical suitability.
