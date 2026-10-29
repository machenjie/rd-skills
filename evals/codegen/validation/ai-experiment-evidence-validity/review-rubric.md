# Review Rubric

## Passing Standard

The candidate implements the deterministic contracts in `task.md`. Public outcomes must pass the executable assertion suite. Source wording and declared success alone are insufficient.

## Scoring

- 50 percent correctness of observed values and diagnostic distinctions.
- 30 percent coverage of duplicate, boundary, and valid neighboring records.
- 20 percent oracle independence, input preservation, and honest proof limits.

## Automatic Failure Conditions

- Treating a success statement as an actual successful terminal state.
- Rejecting every future prediction target as leakage.
- Fitting preprocessing or tuning on final heldout samples.
- Accepting a sequential label without the declared plan constraints.
- The passing fixture fails, or the single-mechanism faulty control is accepted.

## Reviewer Notes

Inspect the actual public-function behavior and assertion independence. Passing these fixed fixtures does not prove production behavior, live model quality, provider semantics, or statistical calibration.
