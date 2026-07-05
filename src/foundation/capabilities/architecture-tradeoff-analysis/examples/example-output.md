# Example Output

```markdown
## ADR-Ready Decision

Status: Proposed
Decision: Keep checkout and billing in one deployable unit but isolate billing behind an internal module interface.

Forces:
- Need transactional consistency during checkout.
- Billing rules change independently from checkout UI.
- Current team cannot support another on-call surface.

Rejected alternatives:
- New billing microservice: rejected because data ownership and failure handling are not ready.
- Shared billing utility: rejected because it would spread policy into multiple modules.

Risks:
- Boundary may erode over time.

Mitigation:
- Add dependency checks and contract tests.

Reassessment trigger:
- Revisit when billing requires independent scaling or release cadence.
```
