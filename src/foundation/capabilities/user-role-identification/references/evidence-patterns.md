# User Role Identification Evidence Patterns

Use this reference when role-inventory closure depends on current source evidence, repository inspection, prior task evidence, observable action sequence, validation freshness, tool permission boundaries, or role-to-validation mapping. Keep it as an evidence map, not a second actor-modeling guide.

## Role Claim-To-Evidence Map

| Role claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Actor exists in the current change | Brief, route/job/webhook/UI entry, source path, policy/doc/test reference, and excluded actor list | The named actor participates in the inspected surface | All adjacent support, admin, machine, or external actors are covered |
| Actor authority is bounded | Subject, resource, action, scope, denied action, tenant/object boundary, and owner | The inventory can feed permission modeling | Enforcement, query scoping, or auth implementation already exists |
| Data visibility is safe to hand off | Visible fields, hidden fields, export/aggregate limits, related-object traversal, and source evidence | Reviewers know what each actor may and may not see | Privacy review, production permission state, or live data access is complete |
| Service or job actor is least privilege | Owner, purpose, credential/auth method, tenant/job/run scope, audit field, and review cadence | Machine blast radius is explicit | Credential rotation, anomaly alerting, or integration reliability is proven |
| External actor trust is explicit | Authentication method, trusted claims, rejected claims, replay/idempotency need, failure behavior, and contract owner | Provider or consumer assertions are bounded | Full integration, signature verification, or provider SLA is verified |
| Support/admin access is purpose bound | Diagnostic read, mutation authority, impersonation, override, export, break-glass, approval, time box, and audit | Privileged human paths are separated for downstream Skills or owners | Compliance approval, production controls, or runbook execution is complete |
| Memory/graph/execution evidence is current | Prior claim source/date, current source reread, graph edge, command/report, exit code/status, and accepted/rejected decision | Old actor knowledge is reconciled with current evidence | Future edits, dynamic policy, or uninspected live provider state stay correct |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, role inventories, generated summaries, incidents, support notes, and execution output as selectors. Confirmation comes from current source, docs, tests, registries, policy files, or owner-controlled artifacts.
- Accept a prior "role exists", "support can access", "service account is scoped", "webhook is trusted", or "tenant boundary is enforced" claim only when current paths and fresh validation still match.
- Mark evidence stale after edits to role policy, route/job/webhook entry points, tenant scoping, support tooling, service accounts, integration contracts, generated clients, fixtures, reports, or validation commands.
- Record inspected and skipped boundaries: actor source, policy file, API route, UI route, job, webhook, service account, IdP/provider, support tool, audit event, test path, report artifact, and production-only control.
- For each final actor-confidence claim, cite a current source path, command, report, test, policy or documentation section, or owner review. An unsupported claim remains unverified with named residual risk.

- If connector, telemetry, production policy, IdP, IAM, or support-tool reads, treat them as external or secret-sensitive, require owner-approved bounded credentials, timestamp, redaction, and evidence-limit disclosure.
- If role policy, permission contract, source, test, or documentation updates, record diff scope, rollback path, validation map, and downstream Skill or owner.

## Blocking Conditions

Block closure when generic actor labels remain, authority lacks subject, resource, action, or scope, or data visibility omits hidden fields or exports. Also block incomplete service-account ownership, merged diagnostic and mutation authority, and external actors without trusted and rejected claim boundaries. Block stale prior evidence, validation predating the final role edit, and state mutation without permission, isolation, and rollback disclosure.
