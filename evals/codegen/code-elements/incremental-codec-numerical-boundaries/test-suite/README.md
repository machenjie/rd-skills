# Test Suite

## Required Checks

Ten assertions cover finite byte partitions, truncation, length limits, partial-write suffixes, units, shapes, convergence, conservation, and independent rod-model applicability and boundary checks.

## Fixtures

`fixtures/passing/subject.py` implements the bounded contract. `fixtures/faulty/subject.py` changes only truncated-EOF handling. `fixtures/faulty-model-domain/subject.py` accepts numerical residual success without model or endpoint validity. The starter leaves decoding incomplete while preserving callable numerical adapters.

## Expected Commands

- `bash ../test-suite/run.sh`

## Regression Cases

Reject truncated EOF, replayed write prefixes, and iteration exhaustion reported as convergence. The rod's source-free discrete residual can be zero for the wrong sourced problem or endpoint conditions; acceptance must still fail. Domain-valid inputs agree with independent analytic interpolation, while a sourced problem's analytic midpoint differs despite the same zero-residual vector. An independent 80-digit decimal reference detects intermediate underflow; a rounded zero cannot satisfy a zero residual budget, and an overflowing residual remains unsuccessful. This validates only the declared fixed model, not real solver or physical-system correctness.
