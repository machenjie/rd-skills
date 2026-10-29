# Test Suite

## Required Checks

Invoke the candidate decoder on finite byte partitions. Assert truncation, length limits, partial-write suffixes, units, shapes, convergence, and conservation.

## Fixtures

`fixtures/passing/subject.py` implements the bounded contract. `fixtures/faulty/subject.py` changes only truncated-EOF handling. The starter leaves decoding incomplete.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Reject accepting truncated EOF as a complete stream. Reject replaying an acknowledged write prefix or treating iteration exhaustion as convergence. The real assertion runner separately executes candidates; smoke alone is not passing-candidate proof.
