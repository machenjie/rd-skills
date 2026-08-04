# Unit Testing Evidence Patterns

Load this reference when closing changed-behavior, denied-outcome, deterministic-seam, double-fidelity, assertion-challenge, cleanup, unit-scope, or selected regression claims. Keep it as an evidence map, not a testing tutorial.

| Claim | Minimum fresh evidence | Proof limit |
| --- | --- | --- |
| Changed local behavior or invariant is proved | Relevant input/state/order/branch, observable allowed and denied outcomes, final command | Other entry points and real integrations remain unproved |
| Selected regression mechanism is locked | Accepted defect, incident, or review finding; causal trigger; observable failure or forbidden effect; counterfactual evidence or limitation; final green command | Adjacent mechanisms and real integrations remain unproved |
| Critical negative outcome is denied | Money/permission/quota/inventory/transition authority, prohibited action, asserted absence of effect | Other entry points and policy layers are not covered |
| Nondeterminism is controlled | Clock/random/identifier/scheduler/environment/global source, seam, owner, reset/advance behavior | Production timing and scheduling remain unproved |
| Double is faithful enough | Required dependency state/error/order/cancel/retry behavior, omitted semantics, rejected real collaborator, follow-up boundary | Real infrastructure and provider contracts are not established |
| Assertion detects the risk | Guard/branch changed by mutation or fault, replayable seed, expected failing assertion, restored final result | Unchallenged branches and unrelated invariants remain unproved |
| Cleanup survives failure | Resources and state created, forced failure/cancel result, cleanup owner, rerun result without contamination | Process crashes and external cleanup need separate evidence |
| Final command is fresh | Current source/test/fixture/double/config paths, command, result, final-edit ordering | Skipped tests and different runtime configurations remain unknown |
| Unit scope is honest | Local behavior proved, skipped boundaries named, next evidence owner, residual risk | System compatibility, concurrency, scale, and production behavior are not inferred |

Treat old test results, reports, coverage notes, prior claims, fixtures, and generated inputs as selectors until current source, test, seam, double, cleanup, and command evidence match the final change. Record skipped entry points and externally owned effects.

Block closure when changed local behavior is unproved, denied behavior is absent, nondeterminism lacks a controlled seam, or a double hides risky semantics. When `regression-testing` is selected, also block closure if the accepted failure mechanism or counterfactual is missing. Also block failed cleanup and unit evidence used to approve a real boundary.
