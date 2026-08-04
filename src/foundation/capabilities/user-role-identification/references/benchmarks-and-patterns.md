# User Role Identification Benchmarks And Patterns

Load this reference when actor trust, authority, data visibility, machine identity, external claims, or support/admin behavior can change the requirement or risk. Do not load it for persona-only research with no system or permission boundary.

## Actor Inventory

| Actor class | Easy-to-miss decisions |
| --- | --- |
| Human/end user | Goal, authentication/trust, tenant/object scope, visible and hidden fields/counts/exports, allowed and denied actions. |
| Support/admin/operator/auditor/incident/data admin | Separate diagnostic read from mutation, impersonation, override, refund, grant/revoke, export, delete, and break-glass; add purpose/approval/audit only as current risk/policy requires. |
| Service account/job/worker/migration/consumer | Named owner/purpose, resource/action/tenant/environment scope, credential lifecycle, run identity, duplicate/replay behavior, audit, and anomaly/cleanup owner. |
| Partner/IdP/webhook/API/file actor | Authentication and verified issuer/source, accepted and rejected claims, tenant mapping, schema/version, replay/idempotency, malformed/expired/unknown failure, and support owner. |

Persona describes motivation, context, and workflow; authorization role defines authority, data scope, and denied behavior. When identifying actors, treat personas, job titles, UI visibility, “trusted internal,” and caller-supplied role, tenant, or status claims as discovery or UX inputs. Do not treat them as authorization authority. Derive permissions from trusted policy inputs and server-side enforcement.

## Visibility And Risk

For each actor distinguish object access, field visibility, aggregates/counts, related-object traversal, create/update/delete/approve/refund/export/import/grant/revoke/override authority, and enforcement boundary. Model denied, wrong-owner, wrong-tenant, stale-role, abuse, support, recovery, and operational paths only where the actor can encounter them.

Support and machine actors are not variants of “admin” or “system.” State the blast radius of leaked credentials or faulty automation. External actors are actors because their claims or consumed data can change durable behavior.

## Evidence And Routes

Inspect current routes, services, policy/query paths, jobs, credentials/config references, contracts, docs, tests, and incident/support evidence in scope. Repository graph proximity cannot prove all entry points; old roles/policies may be stale; an incident signal does not prove the complete actor catalog. Name uninspected surfaces and runtime/external limits.

Reject “all users,” unrestricted support, service identity trusted by location, and webhooks treated as internal events.
Reject UI-only tenant filtering and personas used as policy.
Route subject, resource, and action predicates to `permission-boundary-modeling`.
Route actor paths to `scenario-decomposition` and goals to `use-case-modeling` or `user-flow-modeling`.
Route identity mechanics to `authentication-security` and external actors to `integration-change-builder`.
Route duplicates to `idempotency-retry-design` and adversarial authority to `security-privacy-gate`.
Route executable role proof to `quality-test-gate`.
