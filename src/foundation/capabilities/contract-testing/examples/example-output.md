# Example Output

```markdown
## Contract Compatibility Decision

Surface: `account.updated` event during the v1-to-v2 rollout.
Provider: billing service.
Consumers: analytics loader and notification service; partner consumers remain unknown.

Compatibility risks:
- Retained v1 payloads omit `billing_region`.
- A new status value may reach an older closed-enum consumer.
- Duplicate delivery can replay the same account transition.

Proof:
- Provider verification covers required identifiers, error handling, and v1/v2 payloads.
- Each named consumer parses retained v1 and current v2 fixtures and tolerates unknown status values according to its policy.
- The selected registry check covers the named subject and compared schemas; semantic replay remains covered by consumer cases.

Residual boundary:
- Unknown partner consumers need owner acceptance before the rollout gate can close.
```
