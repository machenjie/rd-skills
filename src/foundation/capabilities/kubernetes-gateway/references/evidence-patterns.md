# Kubernetes Runtime Evidence Patterns

These records separate rendered intent, effective runtime behavior, rollout evidence, and live authority.

## Desired-State Claim

- Record source manifests or package inputs, selected values/profile, rendered artifact, image digest, config/secret references, target cluster/context and namespace, and final-edit freshness.
- Name schema, render, diff, and policy checks actually executed; scope the claim to the selected inputs and supported platform versions.
- Treat rendered output as intended state; record admission, defaulting, controller, custom-resource, hook, and provider behavior that remains unobserved.

## Runtime-Boundary Claim

- Workload evidence names controller kind, lifecycle, state/volume ownership, probes, termination, resources, scaling, placement, disruption, and observed capacity source.
- Identity evidence names service account or workload identity, permissions, secret/config source, network paths, tenant scope, and policy enforcement source.
- Traffic evidence names listener/route/backend, TLS/auth, timeout/retry/body/rate behavior, public or internal exposure, and DNS/edge/load-balancer ownership.

## Rollout And Authority Claim

- Record mixed-version combinations, rollout/watch signals, stop authority, image/config/secret/route/custom-resource/hook reversal, persistent or external state, and forward-recovery owner.
- Distinguish local render or dry-run evidence from live admission, traffic, capacity, secret rotation, and recovery evidence.
- For a live action, record explicit target and authority, expected write scope, redaction, stop condition, and recovery path.
- Close with untested platform versions, traffic paths, capacity conditions, state transitions, provider behavior, and residual ownership.
