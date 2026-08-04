# Unit Testing Decision Patterns

Load this reference when a changed local rule leaves competing behavior-proof, seam, double, assertion-challenge, cleanup, or selected regression designs. These patterns select proof; they do not define system-test policy.

| Decision | Evidence to compare | Reject when |
| --- | --- | --- |
| Selected regression trigger | Accepted defect, incident, or review finding; causal input/state/order; pre-fix behavior; adjacent non-trigger | Selected regression evidence can pass while the original mechanism survives |
| Observable contract | Caller-visible result, error, state, event, or forbidden effect | The assertion observes only test choreography |
| Critical negative proof | Money, permission, quota, inventory, or transition authority and denied result | Success is asserted without proving the prohibited outcome is absent |
| Deterministic seam | Nondeterministic source, control point, reset owner, production-fidelity cost | The seam bypasses the rule or leaks state between runs |
| Double fidelity | Dependency behavior the rule relies on, rejected real collaborator, known fidelity gaps | The double invents impossible state, errors, ordering, cancellation, or ownership |
| Assertion challenge | Guard or branch to invert/remove, seeded fault, expected failing assertion | The challenge changes unrelated behavior or cannot be replayed |
| Failure cleanup | Created resources, changed globals, scheduled work, failure/cancel path, cleanup owner | Cleanup runs only after success or depends on later tests |
| Proof boundary | Local behavior established, real boundaries skipped, next owning evidence | Unit success is reported as integration, compatibility, concurrency, or scale proof |

Mutation and fault seeding are candidate assertion checks for critical or deceptively weak rules, not universal gates. Test doubles are acceptable only for the behavior explicitly represented; their omitted semantics remain a proof limit.

Proof scope: these patterns do not establish database constraints, framework filters, generated-client compatibility, queue delivery, browser behavior, provider semantics, concurrency schedules, or production distribution. Require evidence from the owning boundary before making those claims.
