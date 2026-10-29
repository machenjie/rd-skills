# SaaS Usage, Seats, and Corrections

Load for metered usage, quotas, seat changes, duplicate events, or usage correction.
Skip subscription wording and access changes that do not alter metering or capacity rules.

## Decision Rules

- Define the billable usage fact, subject, unit, period, and stable event identity.
- Separate raw observations from accepted usage and billed aggregates.
- Deduplicate retries using event identity rather than arrival time or equal numeric values.
- Apply late events and corrections according to the target accounting and billing cutoff policy.
- Link corrections to the original fact and preserve how totals changed.
- Distinguish assigned seats, active users, purchased seats, and admission limits.
- Define over-limit behavior for downgrades, concurrent seat assignment, and reactivation.
- Reconcile quota or entitlement projections with accepted usage at the governing period boundary.
- Preserve workspace and subscription identity when organizations merge, split, or change plans.
- Test retries and correction order against an independent total computed from accepted facts.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Same usage event arrives twice | Accepted usage and charges are not duplicated |
| Late event crosses the billing cutoff | Period and correction policy remain explicit |
| Correction follows an earlier aggregate | Recomputation produces the intended corrected total |
| Concurrent assignments exceed purchased seats | Admission or permitted overage follows the product rule |
| Downgrade leaves more assigned seats than allowance | Effective-time and over-limit behavior remain consistent |

## Proof Limits

- Financial reconciliation remains with the financial owner; usage identity does not authorize a charge or refund.
