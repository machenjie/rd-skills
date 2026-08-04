# User Role Identification Decision Checklist

Load this checklist when actor trust, authority, data visibility, machine identity, or external claims affect the task. Do not load it for persona-only wording or a previously accepted unchanged role inventory.

1. Select the mode and define included surfaces, resources, tenants, versions, environments, and excluded actor classes.
2. Record current source, tests, policies, contracts, prior evidence, and validation as accepted, rejected, stale, partial, or unknown.
3. Identify primary and secondary human actors plus the product/system goal each initiates or receives.
4. Separate support, customer/platform admin, operator, auditor, incident responder, and data admin wherever their authority differs.
5. Identify service accounts, jobs, workers, migrations, consumers, and other machine actors.
6. Identify partners, identity providers, webhooks, API/file consumers, and other external actors.
7. Keep behavioral persona context separate from authorization role and policy.
8. For each actor record goal, trust/authentication, allowed and denied actions, and authoritative enforcement boundary.
9. Record visible/hidden fields, counts/aggregates, exports, tenant/object/relationship scope, and existence disclosure.
10. Separate diagnostic read from mutation, override, impersonation, refund, export, delete, grant/revoke, and break-glass authority.
11. For each machine actor record owner, purpose, action/resource/tenant/environment scope, credential lifecycle, run identity, audit, and anomaly/cleanup behavior.
12. For each external actor record verified and rejected claims, tenant mapping, schema/version, replay/idempotency, malformed/expired/unknown failure, and support owner.
13. Map material actor risk to `permission-boundary-modeling` and valid, denied, abuse, recovery, support, and operational scenarios.
14. Name downstream owners, uninspected actor surfaces, external/runtime proof limits, and routes to identity, integration, security/privacy, and executable validation owners.
