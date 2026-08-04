# Authentication Authorization Checklist

- Identify human, workload, partner, delegated, real, and effective subjects plus the authoritative source for each.
- Map the accepted upstream authentication result to the owned internal subject and tenant or organization context.
- Define missing, conflicting, deleted, merged, disabled, or unresolved identity-mapping behavior.
- Mark caller-controlled subject, tenant, delegation, role, group, scope, and assurance fields and the trusted source used instead.
- Preserve actor kind, real/effective relation, authority, relevant bindings, and unresolved context across changed propagation boundaries.
- Identify identity, membership, delegation, tenant, or assurance changes that can stale downstream context and define authoritative re-resolution or failure behavior.
- Specify the minimal authenticated-subject context handed to the permission owner, including authority, tenant semantics, relevant assurance, freshness, and unresolved fields.
- Inspect API, RPC, worker, consumer, callback, admin, support, generated-contract, and audit paths that derive or propagate identity in scope.
- Select applicable missing, conflicting, cross-tenant, misbound, disabled, stale, overwritten, and unattributable-context cases.
- Route credential/session/token lifecycle, replay, recovery, compromise, and assurance-control decisions to `authentication-security`.
- Record external provider state, production mapping data, unknown entry points, and downstream permission enforcement as proof limits with owners.
