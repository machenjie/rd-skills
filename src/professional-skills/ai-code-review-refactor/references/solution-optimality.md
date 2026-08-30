# AI-Generated Choice Check

**Load when:** an AI-generated diff introduces or changes an algorithm, data structure, concurrency model, cache, abstraction, or measurable performance claim.

**Do not load when:** the issue is already a concrete correctness finding, or the diff contains no material implementation choice.

Derive thresholds from the current repository baseline, representative workload, user/business objective, platform policy, and measured evidence; candidate mechanisms and example numbers are not defaults.

## Decision Questions

1. What observable behavior, resource use, or maintenance property changed from the inspected implementation, and which diff/source/test/profile evidence proves that change?
2. Does the generated structure solve a current variation, ownership, scale, or lifecycle constraint, or would direct local code or existing repository behavior satisfy the same acceptance boundary?
3. Did the change alter I/O count, complexity at expected input scale, allocation/cache bounds, blocking, synchronization, cancellation, or error-path cleanup? Require evidence only for reachable deltas.
4. What strongest repository-consistent alternative was inspected, and which measured or contract-backed cost justifies retaining the generated choice rather than simplifying it?
5. If the choice spans broader cost dimensions that this review cannot bound, record the broader tradeoff analysis as unreviewed scope with its evidence need and decision owner.
