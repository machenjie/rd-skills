# Delivery Output And Gates

Use this targeted Reference only when extended release-risk closure needs a gate decision.

## Gate Record

1. **Boundary and artifact:** target plus affected pipeline, artifact, configuration, or secret; immutable build/promotion identity; triggered provenance, reproducibility, and behavior proof.
2. **Rollout and authority:** blast radius, exposure, permission, stop/containment signals, and owned observation selected from consequence and reversibility.
3. **Compatibility and recovery:** coexisting version/data order, skew, consumer behavior, reconciliation, cleanup, and the recovery mechanism with fresh proof.
4. **Infrastructure:** desired/effective diff, authority, state/sync/drift, hooks/CRDs, blast radius, and containment/recovery for IaC, Helm, Kubernetes, or GitOps.
5. **Hotfix or regulated release:** mitigation/resolution owner and signal plus policy-triggered approval, provenance/audit, retention, exception, claim binding, and unproven risk.

## Decision Gates

1. Bind artifact bytes to source/build identity; mutable labels alone cannot establish identity.
2. Prove material environment equivalence across configuration, endpoints, identity, policy, topology, and data shape.
3. Select rollback, restore, repair, disablement, or containment from actual recovery constraints; commands alone are not proof.
4. Give controlled exposure explicit authority, containment signals, and owned observation.
5. Prove coexistence, ordering, reconciliation, cleanup, and rollback readability for triggered migration, contract, or version skew.
6. For effective infrastructure change, inspect diff, state/drift, blast radius, and containment.
7. Carry triggered incident/regulatory evidence; require source evidence for fixed roles or artifacts.

## Proof Limits

- Treat a clean deployment, rollback command, or early cleanup as insufficient for version-skew and recovery claims.
- Before a destructive, production, privileged, or irreversible action, require explicit user authority.
