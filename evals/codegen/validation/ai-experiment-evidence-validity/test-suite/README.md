# Test Suite

## Required Checks

- Retrieval misses differ from answer omissions and unsupported certainty.
- Actual terminal states, uncertainty, and explicit budgets govern trial acceptance.
- Training checks distinguish future targets from unavailable features or immature labels.
- Experiment checks reject SRM, unit mismatch, invalid peeking, and undeclared multiplicity.

## Fixtures

`fixtures/passing` supplies an executable accepted candidate. The named faulty fixture changes one mechanism. `starter-repo` remains deliberately incomplete. Assertion oracles do not import candidate helpers or read expected-result flags from input records.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

- Eight executable assertion methods compare paired valid and invalid records.
- An independent Pearson calculation exposes sample-ratio mismatch.
- A single-mechanism control suppresses only future-feature detection.
- Passing, incomplete starter, and faulty control are run separately.

Default smoke validates starter rejection. The passing fixture and faulty control also require explicit execution through the existing assertion runner.
