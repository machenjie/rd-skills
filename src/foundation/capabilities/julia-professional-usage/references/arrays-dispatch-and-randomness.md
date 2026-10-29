# Julia Arrays, Dispatch, and Randomness

Load for Julia array axes, broadcasting, aliasing, dispatch, or random reproduction decisions.
Skip changes without these Julia runtime contracts.

## Decision Rules

- Inspect the method selected for actual argument types at the affected call.
- Distinguish scalar conversion, promotion, and container element conversion.
- Match array axes to the domain before relying on compatible broadcast dimensions.
- Separate matrix multiplication from elementwise multiplication and fused broadcast expressions.
- Identify shared storage across views, slices, and caller-owned arguments before in-place updates.
- Check whether an operation accepts `missing` and how missingness propagates to predicates or reductions.
- Define NaN and infinity behavior separately from `missing`.
- Pin the project environment and inspect its resolved manifest for reproducible dependencies.
- Record RNG choice, seed, runtime, and execution topology when stochastic results matter.
- Save replay inputs or generated data when comparing cross-version random streams.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Singleton expansion across the wrong axis | Shape validation rejects a legal but unintended broadcast |
| View updated in place | Caller data changes only when ownership permits it |
| Mixed input types select another method | Error and result semantics remain accepted |
| Missing value enters a branch | Policy resolves missingness before Boolean control |
| Same seed on another Julia version | Claim acknowledges random-stream compatibility limits |
| Computation finishes with non-finite values | Validation rejects invalid output despite normal completion |

## Source Limits

- Language-valid broadcasting and numerical stability do not establish model correctness.

## Sources

- [Julia arrays and broadcasting](https://docs.julialang.org/en/v1/manual/arrays/)
- [Julia missing values](https://docs.julialang.org/en/v1/manual/missing/)
- [Julia random generation](https://docs.julialang.org/en/v1/stdlib/Random/)
