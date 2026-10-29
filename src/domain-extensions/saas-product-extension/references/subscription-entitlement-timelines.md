# SaaS Subscription and Entitlement Timelines

Load for trial, grace, plan changes, cancellation, restoration, or refund effects on access.
Skip ordinary tenant queries and one-time payments without subscription state.

## Decision Rules

- Name organization/workspace identity independently from the provider customer or subscription identifier.
- Keep subscription, invoice, payment, and entitlement records separate, with explicit authoritative relationships.
- Derive access from the target product policy for trial, grace, renewal, and termination.
- Record event occurrence, receipt, and entitlement effective times separately.
- Apply upgrades and downgrades at their contractual effective time, including pending changes.
- Bind proration to the product billing basis, period boundaries, rounding, and provider contract.
- Classify end-of-term cancellation separately from immediate cancellation.
- Resolve cancellation and restoration races using authoritative ordering or a versioned state transition.
- Reconcile refund state with the product entitlement policy instead of assuming automatic removal or restoration.
- Preserve the applicable retention or deletion rule when restoring a canceled account.
- Compare reconstructed entitlements with financial and subscription facts after reordered events.

## Failure Probes

| Sequence or probe | Required observation |
|---|---|
| Payment fails while grace remains active | Access follows the grace policy, not payment success alone |
| Downgrade is requested before its effective date | Current entitlements remain until the agreed transition |
| Cancellation and restoration arrive out of order | Authoritative ordering determines the resulting rights |
| Refund arrives after entitlement was granted | Reconciliation applies the defined refund policy |
| Restoration follows a deletion request | Retention and restoration authority are resolved before restoring data |

## Proof Limits

- Business policies, grace durations, and proration rules come from the target product; this Reference supplies no universal defaults.
