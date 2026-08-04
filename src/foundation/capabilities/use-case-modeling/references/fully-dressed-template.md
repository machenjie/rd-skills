# Fully Dressed Use Case Template

Load this template when one actor goal needs a complete, acceptance-testable behavioral contract. Do not load it for implementation design, broad multi-actor journey mapping, or a use case already covered by the root contract and checklist.

```markdown
Use Case ID / Name:
Scope / Level:

Primary Actor:
Secondary Actors or External Systems:
Actor Goal:

Current Evidence:
- accepted:
- rejected or stale:
- unknown and owner:

Stakeholder Interests:
- stakeholder: desired outcome or protected concern

Preconditions:
- fact already true before the trigger

Trigger:

Main Success Path:
1. actor action or externally observable system response

Alternate Paths:
- branch and acceptable outcome

Failure Paths:
- trigger/failure -> safe exit, retry/compensation/support owner

Minimum Guarantee When Goal Fails:
- durable state, events, side effects, and information exposure

Success Guarantee:
- durable state, events, side effects, and externally visible result

Postconditions:
- success:
- failure/partial:

Business Rules And Permission Boundaries:
- rule/policy owner and denied behavior

Acceptance / Test Trace:
- path or guarantee -> criterion/evidence

Proof Limits And Handoffs:
- production/external/stakeholder unknown, residual owner, routed capability
```

Keep the path behavioral: do not prescribe tables, queues, providers, retry counts, timeouts, or other implementation choices unless a current contract or stakeholder-owned policy makes them constraints. One use case may reference a lifecycle or permission model but does not replace those specialist artifacts.
