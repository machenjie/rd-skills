# State, Plan, And Drift Contracts

Use for state authority, coordination, drift, unknowns, or proposal freshness; it excludes mutation authority.

Sources accessed 2026-07-24.

## State Boundary

| Surface | Bind |
| --- | --- |
| Desired | Source and immutable revision. |
| Recorded | Backend, workspace/stack, version, encryption, recovery owner. |
| Provider | Remote identity, drift scope, unsupported fields, observation time. |
| Effective | Admitted, reconciled, serving, external effects. |
| Coordination | Lock/lease/field owner/controller/single writer and failure behavior. |
| Proposal | Artifact, source/state/target/versions/time/unknowns/omissions. |

## Tool Boundaries

- **Terraform:** inspect state mapping, locking, plan unknowns, reference dependencies, and dependency locks separately.
- **OpenTofu:** verify backend/locking, plan mode, encryption, and dependency locks.
- **Pulumi:** inspect backend/state, stack, refresh stance, and plan unknowns.
- **CloudFormation:** separate template/parameters, stack state, drift coverage, executable and drift-aware change sets.
- **Kubernetes:** separate objects, field ownership, status, controller reconciliation, and external effects.
- **Helm:** resolve values, dependencies, hooks, and CRDs before upgrade output.
- **Kustomize:** inspect overlay and transformed identities.

## Official Evidence

- Terraform: <https://developer.hashicorp.com/terraform/language/state/purpose> <https://developer.hashicorp.com/terraform/language/state/locking> <https://developer.hashicorp.com/terraform/cli/commands/plan> <https://developer.hashicorp.com/terraform/language/expressions/references> <https://developer.hashicorp.com/terraform/language/files/dependency-lock>
- OpenTofu: <https://opentofu.org/docs/language/state/backends/> <https://opentofu.org/docs/language/state/locking/> <https://opentofu.org/docs/cli/commands/plan/> <https://opentofu.org/docs/language/state/encryption/> <https://opentofu.org/docs/language/files/dependency-lock/>
- Pulumi: <https://www.pulumi.com/docs/reference/state/> <https://www.pulumi.com/docs/iac/operations/stack-management/update-plans/>
- CloudFormation: <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html> <https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html>
- Kubernetes: <https://kubernetes.io/docs/concepts/overview/working-with-objects/> <https://kubernetes.io/docs/reference/using-api/server-side-apply/> <https://kubernetes.io/docs/concepts/architecture/controller/>
- Helm: <https://helm.sh/docs/topics/charts_hooks/> <https://helm.sh/docs/helm/helm_upgrade/>
- Kustomize: <https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/>

## Non-Equivalence Rules

- Keep Terraform/OpenTofu plans, Pulumi plans, CloudFormation sets, Kubernetes dry-run, Helm renders, and Kustomize builds distinct.
- Do not project OpenTofu encryption onto Terraform, Pulumi, CloudFormation, Kubernetes Secrets, or Helm output.
- Do not infer live drift from render or convergence from accepted desired state.
- Refresh evidence after a bound source/state/target/version/provider/dependency or relevant-time change.

## Proof Limits

- OpenTofu pages identify 1.12 and Helm pages 4.2.2 where stated; others are rolling.
- Sources do not prove repository versions, backends, providers, admission, live drift, production authority, or apply results.

## Anti-Patterns

- Proposals are not execution/convergence proof; source rollback may leave effects.
