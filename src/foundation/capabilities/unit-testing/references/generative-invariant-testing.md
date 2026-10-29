# Generative Invariant Testing

**Reference type:** targeted
**Load when:** A real input combination space or state sequence needs property, metamorphic, or model-based testing.
**Do not load when:** A small set of established examples already proves the local contract without a meaningful exploration gap.
**Required by:** analysis-agent, task-agent, review-agent
**Required output:** decision-record, validation-plan, proof-limit

## Property Design

- Derive each property from a public contract, invariant, reference model, or justified mathematical relation.
- Keep the oracle independent of the implementation under test. Repeating its calculation or parsing logic can preserve the same defect.
- Separate legal input generation from invalid-input generation. Invalid values need a rejection or recovery oracle, not an undefined success property.
- Generate meaningful boundary combinations directly. Excessive rejection can hide sparse valid cases and exhaust the exploration budget.
- Define metamorphic relations from domain semantics. An arbitrary input transformation does not imply equivalent output.
- Compare normalized meaning when the format permits normalization. Byte-exact round trips are valid only when the contract requires them.
- Use a small state model when correctness depends on operation history. Generate only legal commands unless testing explicit invalid transitions.
- Check results and state invariants after meaningful transitions. Include duplicate, cancellation, expiry, and recovery transitions when the contract admits them.
- Shrink while preserving the preconditions that expose the defect. An invalid smaller case is not the same counterexample.
- Retain the minimized input or command sequence with relevant versions and configuration. A seed alone may not reproduce across tool changes.
- Bound trials, generated size, sequence length, and runtime from the required exploration and available resources.
- Promote a discovered mechanism to a stable regression example. Keep broader generation where it still explores distinct behavior.

## Distinguishing Examples

| Contract | Useful property or sequence | Invalid substitute |
| --- | --- | --- |
| Allocate a fixed total under the required rounding rule | Allocations conserve the total and satisfy allowed precision and bounds | Recompute expected shares with the production allocation code |
| Encode a format that permits canonicalization | Decode/encode preserves defined meaning after normalization | Demand identical bytes for equivalent permitted encodings |
| Reserve, cancel, retry, and expire resources | The model preserves valid ownership and resource conservation | Generate impossible histories, then discard their failures |
| Shrink an ordered transaction sequence | Retain prerequisites for the failing transition | Remove its creation step and report the unrelated missing-object error |
| Compare scaled numerical inputs | Use a relation justified by the modeled operation and error budget | Assume every operation is linear |

Return the property source, generator domain, oracle, minimized counterexample, replay inputs, and exploration bounds.
Passing a finite generated sample does not prove all inputs, schedules, or real dependency behavior.

## Tool-Specific Sources

- For Hypothesis, check [stateful models](https://hypothesis.readthedocs.io/en/latest/stateful.html) and [constrained strategies](https://hypothesis.readthedocs.io/en/latest/tutorial/custom-strategies.html).
- Preserve state preconditions during shrinking as a test-design obligation, not an assumed guarantee from a generator library.
- Keep permanent regression inputs alongside the [replay mechanism](https://hypothesis.readthedocs.io/en/latest/tutorial/replaying-failures.html). Seed replay depends on strategies, versions, and external nondeterminism.
- Treat `reproduce_failure` blobs as temporary, exact-version aids rather than a durable input format.
