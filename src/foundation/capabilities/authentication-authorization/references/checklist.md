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
