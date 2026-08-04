# CI/CD Pipeline Benchmarks And Patterns

Load this reference only after `delivery-release-gate` and `release-rollback` provide an accepted release and recovery contract. Compare provider enforcement, supply-chain, IaC/Helm, monorepo, and evidence mechanisms that can encode it. Route open approval, rollout, observation, stop, containment, or recovery decisions to those owners.

## Pipeline And Promotion Decisions

| Surface | Required decision | Evidence and conditional gate |
| --- | --- | --- |
| Pre-merge | Fast feedback for changed behavior, policy, secrets, and formatting. | Required checks reflect changed risk; quarantined flakes retain an owner and replacement signal. |
| Trunk/build | Full behavioral/security/license checks and one reproducible artifact. | Lock/source inputs, SBOM, scan, signature/provenance, digest, and failure owner are current. |
| Test/staging | Promote the same artifact by default and validate integration, config, migration, and rollback assumptions. | A per-environment rebuild requires an explicit equivalence contract proving source revision, behavior-affecting inputs, provenance, output identity, and rollback mapping. |
| Production | Encode the accepted approval, window, exposure, observation, stop, and recovery contract. | Provider controls preserve its metric/source/duration/owner/deadline and artifact/environment identity before mutation. |
| Post-deploy | Capture the accepted user/dependency watch and recovery evidence. | Failure invokes the accepted rollback/forward-fix action; “deploy succeeded” alone is not closure. |

## Deployment Strategy

Use these rows to verify provider support for the accepted strategy or expose a representation gap. They do not select rollout or recovery policy.

| Strategy | Use when | Required rollback proof |
| --- | --- | --- |
| Recreate | Downtime and full exposure are accepted for the current environment/state. | Prior artifact/state and user-impact window. |
| Rolling | Mixed versions are compatible and readiness removes unsafe instances. | Old/new code, schema, config, and route compatibility. |
| Blue/green | Parallel capacity and traffic switch reduce cutover risk. | Switch-back path plus shared-state compatibility. |
| Canary | A bounded cohort produces meaningful health evidence before expansion. | Exposure steps, guardrail metrics, stop condition, and rollback owner. |
| Shadow/mirror | New behavior can be compared without serving its result. | Privacy, side-effect suppression, divergence metric, and cost owner. |
| Feature flag | Release can be separated from deployment by client/tenant/cohort. | Safe default, propagation, telemetry, rollback, and cleanup owner. |

## Supply Chain, IaC, And Build Correctness

- Pin mutable third-party actions, dependencies, base/release images, and generated inputs according to current provenance policy; use short-lived scoped credentials where the platform supports them.
- Produce SBOM, vulnerability/license results, signature/provenance, and immutable artifact identity when the release risk or policy requires them. Thresholds come from current policy and reachability, not this reference.
- IaC plan evidence identifies the target environment and commit, apply authority, recovery path, and applicable state-lock or drift implications. It also identifies applicable destructive, IAM, or cost implications. A clean plan alone does not prove safe apply.
- Helm/GitOps evidence includes locked dependencies, values/schema validation, rendered manifests per supported environment, policy/diff review, upgrade health behavior, CRD/hook ordering, and rollback limitations.
- Map changed files to direct modules, dependents, contracts, generated inputs, and artifacts in monorepo selection.
- Include every behavior-affecting input in cache keys.
- State the full-suite fallback.

## Evidence Limits And Rejections

- Fresh evidence follows the final workflow, lockfile, cache-key, generated-input, permission, registry, validator, or build change. Record whether commands are read-only or mutate deploy, cloud, package, or infrastructure state.
- Local builds and static checks do not prove hosted-runner permissions, credentials, live admission/IAM, provider behavior, production capacity, or rollout success.
- Reject mutable production artifacts, long-lived broad deploy credentials, and per-environment rebuilds lacking that explicit equivalence contract.
- Reject required checks hidden by continue-on-error or retry-to-green.
- Reject unreviewed IaC apply and missing post-deploy health evidence.
- Reject emergency overrides without an owner, expiry, and audit record.
