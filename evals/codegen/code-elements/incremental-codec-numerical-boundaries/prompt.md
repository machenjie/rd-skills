# Benchmark Prompt

## Task

Complete the deterministic fixture adapters in `subject.py`. This is validation infrastructure with an accepted contract, not a product transport or numerical runtime.

## Context

The suite checks incremental frame parsing, partial writes, and small numerical invariants. It uses Python standard-library functions and controlled inputs.

## Requirements

- `decode_frames(chunks, max_frame=256, max_total=1024, eof=True)` parses unsigned varint byte lengths followed by UTF-8 payloads. A prefix has at most three bytes. A continuation bit on its third byte is invalid.
- Return `(frames, status)`, where status is `complete` or `need-more`. Incomplete input is allowed when `eof=False`; EOF inside a prefix or payload raises `ValueError`.
- Enforce frame and cumulative payload-byte bounds before consuming an oversized payload. Empty frames are valid. Invalid UTF-8 raises `ValueError`.
- `write_all(payload, sink)` resumes at each acknowledged suffix and returns total bytes. Zero, negative, or oversized progress raises `ValueError`.
- `length_metres(vector, unit)` accepts three finite coordinates in metres. Other units, shapes, or non-finite values raise `ValueError`; large finite norms retain the tested relative accuracy.
- `sqrt_result(value, max_iterations=100, relative_budget=1e-12)` returns `(estimate, converged)`. Reject negative or non-finite values and invalid budgets. Exhausting iterations is not convergence.
- `allocate(total, weights)` uses nonnegative integer quantities and positive total weight. Apply largest remainders, breaking ties by index, while conserving the integer total.

## Constraints

Use no network, dependencies, clocks, or external state. Tests supply expected outcomes independently. Fixture tolerances belong to these examples, not all numerical work.

## Deliverables

Implement the candidate adapters and retain the existing callable interfaces. Explain unproved transport, numerical, and environmental behavior.

## Completion Evidence

Run the passing candidate assertions and reject both the incomplete starter and the truncated-EOF faulty control. Finite partitions and input ranges are bounded evidence.
