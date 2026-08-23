# Test Data Management Evidence Patterns

Use this evidence map for a named fixture ownership, cleanup, privacy, determinism, parallel-safety, freshness, or proof-limit claim; it is not another fixture catalog.

## Surface-To-Validation Map

| Claim | Minimum current evidence | Proves / limit |
| --- | --- | --- |
| Owned fixture | Artifact, consumers, asserted fields, defaults/traits, update/deletion owner. | Bounded purpose; not future schema or hidden consumers. |
| Isolated effects | Side-effect inventory, namespace/transaction/container, cleanup, parallel review. | Inspected reset path; not every shard, delayed job, or sandbox. |
| Privacy-safe data | Category, synthetic/sanitized rule, scan/review, retention owner. | Selected patterns absent; not every identifier, free-text leak, or historic artifact. |
| Determinism | Clock/random/ID/locale/order controls, seed, rerun, failure signature. | Named values reproducible; not every async/environment flake. |
| Parallel/volume partition | Worker/VU scope, slice, collision check, cleanup/retention, quota. | Named collisions bounded; not production scale, every quota, or long retention. |
| Fresh evidence | Current schema/fixture/test/CI paths, prior-claim decision, validator/report, final-edit freshness. | Inspected source matches; not later edits. |

## Evidence Quality

- Strong: current artifacts, command/review status, final-edit freshness, and proof limits.
- Weak: old CI, global convention, unscoped reuse, memory, or cleanup review without side-effect inventory.
- Missing: no owner, cleanup, classification, seed, parallel statement, or inaccessible-sandbox owner.
- Invalid: real secret/PII, unguarded shared reset, asserted unseeded randomness, or stale memory treated as current.

## Tool Boundary And Handoff

- Destructive cleanup or sandbox reset needs owned isolation, dry-run/staging proof, stop, and restore/reseed.
- Protected exports/scans need approved source, minimization/redaction, retention/deletion, and cross-namespace proof.
- Record inspected paths; accepted and stale claims; surface, risk, artifact/status, proves/does-not-prove, and owner; mutation/redaction boundary; residual risk and next gate.
