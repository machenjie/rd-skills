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
- `rod_evidence(problem, temperatures, residual_budget=1e-10, boundary_budget=1e-10)` checks a fixed steady one-dimensional, source-free rod model with constant positive conductivity, positive length, a uniform grid of at least three temperatures, and two prescribed-temperature endpoints. The independent analytic solution in this domain is linear interpolation between the endpoint temperatures.
- The problem record supplies `length_m`, `conductivity`, `heat_source`, and `left`/`right` records with `kind` and `value`. Length is in metres, conductivity in W/(m K), distributed heat source in W/m³, and prescribed temperatures in kelvin. Reject inputs outside finite floating-point representation, a grid spacing that underflows to zero, and invalid tolerances with `ValueError`.
- Compute the selected source-free model's maximum interior residual `abs(k * (T[i-1] - 2*T[i] + T[i+1]) / dx**2)`. Compare the unrounded residual of the supplied numeric values against the residual budget in W/m³; intermediate underflow must not turn a failed residual into success. Report `residual` rounded to a float (infinity if it exceeds that output range) and the independently computed `numerical_pass`. Rounded output, including zero, is not the budget authority. Separately derive `applicable` from zero actual heat source and two `temperature` boundary kinds, and `boundary_pass` from applicability and endpoint agreement within the boundary budget in kelvin. `accepted` requires all three checks. A zero residual for this model cannot validate a sourced problem or the wrong endpoints; no supplied `model_valid` flag is accepted.

## Constraints

Use no network, dependencies, clocks, or external state. Tests supply expected outcomes independently. Fixture tolerances belong to these examples, not all numerical work.

## Deliverables

Implement the candidate adapters and retain the existing callable interfaces. Explain unproved transport, numerical, and environmental behavior.

## Completion Evidence

Run the passing candidate assertions and reject the incomplete starter, truncated-EOF fault, and residual-only model-acceptance fault. Finite partitions and input ranges are bounded evidence. The rod checks establish only this declared model and independent analytic comparisons, not the validity of a real scientific solver or other physical regimes.
