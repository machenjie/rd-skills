# Identity, Destruction, And Recovery Contracts

Use this reference when resource identity, graph scope, replacement, destruction, protection, recovery, or secret exposure changes the decision. Do not use it to execute import, move, apply, replace, rollback, or destroy operations.

Official sources were accessed on 2026-07-24.

## Decision Record

| Concern | Required decision |
| --- | --- |
| Identity | Bind source address or logical name to remote identity, current owner, target, and state record. |
| Graph | Record dependencies, field or controller owners, hooks, custom resources, generated names, and effects omitted by targeting. |
| Outcome | Classify create, adopt, import, move, update, replace, destroy, orphan, retain, prune, and external side effects. |
| Security | Record privilege, trust, public network, secret-bearing artifact, deletion protection, and key-recovery changes. |
| Recovery | Select source revert, state repair, remote restore, compensation, or forward reconciliation for each changed surface. |

## Tool Deltas

- **Terraform:** verify remote identity before import or move, then inspect lifecycle and recovery limits; see [import](https://developer.hashicorp.com/terraform/language/import), [moved blocks](https://developer.hashicorp.com/terraform/language/block/moved), [lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle), and [state recovery](https://developer.hashicorp.com/terraform/cli/state/recover).
- **OpenTofu:** verify selected-version identity declarations, targeting, backend, and encryption-key recovery without inferring Terraform move, import, lifecycle, or recovery behavior from shared syntax.
- **Pulumi:** bind logical and physical names, aliases, protection, replacement order, backend, and secret handling; see [names](https://www.pulumi.com/docs/iac/concepts/resources/names/), [aliases](https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/), [protect](https://www.pulumi.com/docs/iac/concepts/resources/options/protect/), and [secrets](https://www.pulumi.com/docs/iac/concepts/secrets/).
- **CloudFormation:** separate logical and physical identity, stack policy, termination protection, replacement behavior, and failed-rollback recovery; see [stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html), [termination protection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html), and [continue update rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html).
- **Kubernetes:** inspect object identity, field ownership, owner references, controllers, prune scope, finalizers, and achieved external effects; see [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/), [declarative management](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/), and [operator pattern](https://kubernetes.io/docs/concepts/extend-kubernetes/operator/).
- **Helm:** treat hooks, CRDs, generated Secrets, and external effects as separate lifecycle surfaces; see [upgrade](https://helm.sh/docs/helm/helm_upgrade/), [rollback](https://helm.sh/docs/helm/helm_rollback/), [hooks](https://helm.sh/docs/topics/charts_hooks/), and [CRDs](https://helm.sh/docs/chart_best_practices/custom_resource_definitions/).
- **Kustomize:** compare final names, namespaces, selectors, generators, hashes, and patches; a build has no state lock, drift repair, protection, or rollback semantics.

## Failure Rules

- Require omitted dependency and reconciliation boundaries before treating a targeted proposal as complete graph evidence.
- Reject deletion protection as recovery proof; it may block one operation without restoring state, data, permissions, routes, or external effects.
- Classify state recovery as tracking repair rather than remote reversal while provider resources can remain changed.
- Redact secret values from state, plans, previews, renders, logs, diffs, and evidence; route rotation, revocation, and exposure response to `secret-configuration-security`.
- Route data transformation to `data-migration-design`, provider policy to `cloud-platform-extension`, and release or rollback approval to `delivery-release-gate`.

## Source Limits

- Tool and service pages are rolling unless they state a version; provider, resource, cluster, chart, plugin, and backend behavior remains version-specific.
- These sources do not prove remote identity, authorization, deletion safety, secret non-exposure, rollback success, external-effect reversal, or production recovery.
