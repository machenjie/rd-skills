# Example Output

```markdown
## Architecture Style Decision

Selected style: Modular monolith with explicit billing and fulfillment modules.

Reason:
- Independent deployment is not required yet.
- Shared transaction boundary is still valuable.
- Team ownership can be enforced through module contracts and dependency rules.

Rejected alternative: Split billing into a microservice now.
Rejection reason: The API contract, observability, incident ownership, and data consistency plan are not mature enough to justify network and deployment overhead.

Risks:
- Module boundaries may drift without dependency checks.
- Future scale pressure may require a service extraction path.

Mitigations:
- Define module interfaces and dependency direction.
- Keep billing persistence isolated enough for a later split.

Quality gate: Simpler modular design satisfies current constraints and preserves a future extraction option.
```
