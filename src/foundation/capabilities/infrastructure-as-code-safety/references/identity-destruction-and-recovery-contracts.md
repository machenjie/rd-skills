# Identity, Destruction, And Recovery Contracts

Use for identity, graph, destruction, recovery, or secret exposure; it excludes mutation authority.

Sources accessed 2026-07-24.

## Required Record

| Concern | Bind |
| --- | --- |
| Identity | Source/logical address, remote identity, owner, target, state record. |
| Graph | Dependencies, field/controller owners, hooks/resources, names, targeting omissions. |
| Outcome | Create, adopt/import/move, update/replace/destroy, orphan/retain/prune, external effects. |
| Security | Privilege/trust/network, secret artifacts, deletion protection, key recovery. |
| Recovery | Source revert, state repair, remote restore, compensation, or forward reconciliation per surface. |

## Tool Boundaries

- **Terraform:** verify pre-import/move identity, lifecycle, and state recovery.
- **OpenTofu:** verify selected-version identity, targeting, backend, encryption-key recovery, and Terraform differences.
- **Pulumi:** bind logical/physical names, aliases, protection, replacement order, backend, and secrets.
- **CloudFormation:** separate logical/physical identity, stack policy, termination protection, replacement, and failed-rollback recovery.
- **Kubernetes:** inspect identity, field/owner/controller authority, prune/finalizers, declarative lifecycle, and external effects.
- **Helm:** separate upgrade/rollback, hooks, CRDs, generated Secrets, and external effects.
- **Kustomize:** compare transformed identities; its build has no lock, drift repair, protection, or rollback.

## Official Evidence

- Terraform: <https://developer.hashicorp.com/terraform/language/import> <https://developer.hashicorp.com/terraform/language/block/moved> <https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle> <https://developer.hashicorp.com/terraform/cli/state/recover>
- Pulumi: <https://www.pulumi.com/docs/iac/concepts/resources/names/> <https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/> <https://www.pulumi.com/docs/iac/concepts/resources/options/protect/> <https://www.pulumi.com/docs/iac/concepts/secrets/>
- CloudFormation: <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html> <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html> <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html>
- Kubernetes: <https://kubernetes.io/docs/concepts/overview/working-with-objects/> <https://kubernetes.io/docs/tasks/manage-kubernetes-objects/declarative-config/> <https://kubernetes.io/docs/concepts/extend-kubernetes/operator/>
- Helm: <https://helm.sh/docs/helm/helm_upgrade/> <https://helm.sh/docs/helm/helm_rollback/> <https://helm.sh/docs/topics/charts_hooks/> <https://helm.sh/docs/chart_best_practices/custom_resource_definitions/>

## Failure Rules

- Require omitted-dependency and reconciliation boundaries before accepting targeted evidence as complete-graph evidence.
- Treat deletion protection as one-operation blocking, not recovery of state, data, permissions, routes, or external effects.
- Treat state recovery as tracking repair while remote resources may remain changed.
- Redact secrets from state/proposals/renders/logs/diffs/evidence; route exposure to `secret-configuration-security`.
- Route transformation to `data-migration-design`, provider policy to `cloud-platform-extension`, and approval to `delivery-release-gate`.

## Proof Limits

- Sources are rolling unless versioned; behavior remains tool/provider/resource/cluster/chart/plugin/backend-version specific.
- Sources do not prove identity, authorization, deletion safety, non-exposure, rollback, external reversal, or production recovery.
