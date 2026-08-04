# Kubernetes Runtime Checklist

- Name target cluster/context, namespace, controller/workload kind, process lifecycle, state ownership, and mutation authority.
- Define startup, readiness, liveness, drain, termination, and in-flight-work outcomes from the failures each signal can correct.
- Derive requests, limits, scaling, disruption, topology, priority, and scale-down behavior from workload and capacity evidence.
- Bind workload identity, service account, permissions, cloud identity, secret/config source, ingress, egress, and tenant scope.
- Specify listener, route, backend, TLS/auth, timeout/retry/body/rate behavior, and external DNS/edge ownership that change.
- Tie rendered manifests, image digest, config/secret versions, policies, routes, and target environment to one release identity.
- Inspect defaulting, admission, controller, custom-resource, hook, persistent-state, and external-provider effects outside rendered intent.
- Define mixed-version behavior, watch and stop signals, reversal or forward recovery, and partial-mutation handling.
- Record fresh render/policy proof, live behaviors not exercised, authority boundary, and residual owner.
