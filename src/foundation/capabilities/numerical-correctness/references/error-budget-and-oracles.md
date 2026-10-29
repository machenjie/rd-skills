# Numerical Error Budgets and Oracles

Load for tolerance, conditioning, reduction, mixed-precision, or numerical-oracle decisions.
Skip ordinary decimal accounting and changes without numerical computation.

## Decision Rules

- Record units, shape, valid domain, and the quantity whose error matters.
- Separate input uncertainty from discretization, approximation, and floating-point error.
- Estimate sensitivity before blaming precision for an ill-conditioned problem.
- Check cancellation and intermediate overflow even when the final mathematical value is representable.
- Compare error in the same units as the accepted quantity.
- Use absolute bounds near zero and relative bounds where the reference scale supports them.
- Specify how NaN, infinities, signed zero, and subnormal values affect acceptance.
- Compare reduction orders and batch partitions when parallel accumulation changes results.
- Test accumulation precision separately from storage and multiplication precision.
- Establish the oracle's own error and domain before treating it as ground truth.
- Use conservation, symmetry, monotonicity, or transformations only when the mathematical contract entails them.
- Report random variation separately from deterministic numerical error.

## Failure Probes

| Probe | Required distinction |
|---|---|
| Incompatible units or shape | Representation compatibility does not establish mathematical validity |
| Small nonzero result near zero | A default absolute tolerance can hide a material error |
| Large terms nearly cancel | Relative error can grow despite finite inputs |
| Reordered or partitioned reduction | Compare against the task error budget, not assumed associativity |
| Mixed precision over a long accumulation | Check intermediate range and aggregate drift |
| Same seed on another device or version | Bound reproduction to the declared environment |

## Source Limits

- NumPy `isclose` scales its relative term by the second argument; its default absolute tolerance can mislead near zero.
- Numerical agreement alone does not validate the physical, statistical, or business model.
- PyTorch development documentation describes behavior that must be checked against the installed release.

## Sources

- [NumPy comparison semantics](https://numpy.org/doc/stable/reference/generated/numpy.isclose.html)
- [PyTorch numerical accuracy](https://docs.pytorch.org/docs/main/notes/numerical_accuracy.html)
- [PyTorch reproducibility limits](https://docs.pytorch.org/docs/main/notes/randomness.html)
