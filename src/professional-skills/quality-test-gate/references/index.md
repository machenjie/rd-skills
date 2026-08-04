# Quality Test Gate Reference Index

Reference type: index
Load when: choosing among local references that could change the current validation decision.
Do not load when: the root contract or a named reference already identifies the needed material.

| Reference | Load when | Do not load when |
| --- | --- | --- |
| [checklist.md](checklist.md) | Ordinary acceptance-to-test mapping needs a compact checklist. | The root checklist already covers the bounded change. |
| [test-output-and-gates.md](test-output-and-gates.md) | Migration, security, release, concurrency, or multi-boundary proof needs deeper calibration. | A local targeted test is sufficient. |
| [test-structure-boundaries.md](test-structure-boundaries.md) | Fixtures, mocks, golden data, shared helpers, private access, or test placement affect correctness. | No test-structure decision exists. |
| [example-output.md](../examples/example-output.md) | A concise output example helps shape the handoff. | Example wording could be mistaken for current evidence. |
