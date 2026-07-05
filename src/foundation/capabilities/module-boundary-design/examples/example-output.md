# Example Output

```markdown
## Module Boundary Map

Module: Subscription Management
Capability: Owns subscription lifecycle, plan changes, cancellation rules, and renewal eligibility.

Public interface:
- request_plan_change(account_id, plan_id)
- cancel_subscription(subscription_id, actor_id)

Private internals:
- Subscription aggregate
- Renewal policy
- Subscription persistence mapping

Allowed dependencies:
- Billing interface for invoice preview
- Account identity interface for tenant ownership

Forbidden dependencies:
- Direct imports from billing repositories
- Direct reads of billing tables

Enforcement:
- Dependency rule rejects subscription -> billing.infrastructure imports.
- Contract tests cover billing interface responses.
```
