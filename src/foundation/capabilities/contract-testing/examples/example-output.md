# Example Output

```markdown
## Contract Test Plan

Contract: account.updated event v2.

Provider: billing-service.
Consumers: analytics-loader, notification-service.

Checks:
- Schema registry compatibility remains backward compatible.
- `account_id`, `status`, and `occurred_at` are required.
- Unknown fields are ignored by consumers.
- New `billing_region` field is optional for v2 rollout.
- Invalid enum value fails provider contract test.

Release gate:
- Provider verification and two consumer fixtures pass in CI.
```
