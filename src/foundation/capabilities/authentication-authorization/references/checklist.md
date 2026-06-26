# Authentication Authorization Checklist

- Identify how identity is proven and propagated.
- Separate authentication decisions from authorization decisions.
- List subjects, actions, resources, tenant scope, ownership scope, and conditions.
- Enforce object-level authorization for resource-specific operations.
- Confirm backend checks do not depend on hidden frontend controls.
- Deny by default when policy context is incomplete.
- Define unauthenticated, unauthorized, and not-found response behavior.
- Audit sensitive allow, deny, escalation, and administrative actions.
- Define permission cache invalidation for role, membership, or ownership changes.
- Add tests for allowed, denied, cross-tenant, missing-resource, and stale-permission cases.
- Record source paths, entry-point graph, project-memory claims, generated contracts, and validation freshness.
- Map each protected operation to object rule, PDP/PEP placement, denial behavior, audit event, cache/claim invalidation, and positive/negative tests.
- State what the authorization plan does not prove: uninspected entry points, production policy state, stale tokens, generated clients, manual approvals, and future role changes.
