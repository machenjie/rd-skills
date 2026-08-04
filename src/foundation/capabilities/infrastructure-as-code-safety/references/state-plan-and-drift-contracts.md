# State, Plan, And Drift Contracts

Use this reference when the selected tool changes state authority, coordination, drift, unknown-value, or proposal-freshness decisions. Do not use it as permission to mutate infrastructure.

Official sources were accessed on 2026-07-24.

## State Boundary

| Surface | Decision |
| --- | --- |
| Desired source | Name the final module, template, program, object, chart values, or overlay and its immutable revision. |
| Recorded state | Name the backend, workspace or stack, state version, encryption boundary, and recovery owner when the tool records state. |
| Provider state | Record the observed remote identity, refresh or drift scope, unsupported fields, and observation time. |
| Effective state | Separate admitted, reconciled, serving, and externally visible effects from submitted intent. |
| Coordination | Identify the supported lock, lease, field owner, controller, or single-writer rule and its failure behavior. |
| Proposal | Bind the plan, preview, change set, render, or diff to source, state, target, versions, time, unknowns, and omissions. |

## Tool Deltas

- **Terraform:** inspect state mapping, backend locking, provider locks, unknown values, and targeting separately; see [state purpose](https://developer.hashicorp.com/terraform/language/state/purpose), [locking](https://developer.hashicorp.com/terraform/language/state/locking), [plan](https://developer.hashicorp.com/terraform/cli/commands/plan), [references](https://developer.hashicorp.com/terraform/language/expressions/references), and [dependency locks](https://developer.hashicorp.com/terraform/language/files/dependency-lock).
- **OpenTofu:** verify backend locking, plan mode, dependency locks, and key recovery; see [backends](https://opentofu.org/docs/language/state/backends/), [locking](https://opentofu.org/docs/language/state/locking/), [plan](https://opentofu.org/docs/cli/commands/plan/), [encryption](https://opentofu.org/docs/language/state/encryption/), and [dependency locks](https://opentofu.org/docs/language/files/dependency-lock/).
- **Pulumi:** inspect the selected backend, stack state, refresh stance, and update-plan unknowns; see [state and backends](https://www.pulumi.com/docs/reference/state/) and [update plans](https://www.pulumi.com/docs/iac/operations/stack-management/update-plans/).
- **CloudFormation:** separate template, parameters, stack state, drift coverage, and executable change set; see [change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html) and [drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html).
- **Kubernetes:** separate submitted objects, field ownership, observed status, controller reconciliation, and external effects; see [objects](https://kubernetes.io/docs/concepts/overview/working-with-objects/), [controllers](https://kubernetes.io/docs/concepts/architecture/controller/), and [Server-Side Apply](https://kubernetes.io/docs/reference/using-api/server-side-apply/).
- **Helm:** resolve values, dependencies, hooks, and CRDs before interpreting the final render; see [upgrade](https://helm.sh/docs/helm/helm_upgrade/) and [chart hooks](https://helm.sh/docs/topics/charts_hooks/).
- **Kustomize:** inspect the selected overlay and final transformed identities; see [bases, overlays, and generators](https://kubernetes.io/docs/tasks/manage-kubernetes-objects/kustomization/).

## Non-Equivalence Rules

- Treat Terraform and OpenTofu plans, Pulumi update plans, CloudFormation change sets, Kubernetes dry-run behavior, Helm renders, and Kustomize builds as different evidence classes.
- Do not project OpenTofu state encryption onto Terraform, Pulumi secret handling, CloudFormation storage, Kubernetes Secrets, or rendered Helm output.
- Do not infer live drift coverage from a render, or controller convergence from accepted desired state.
- Refresh proposal evidence after any bound source, state, target, version, provider, dependency, or relevant elapsed-time change.

## Source Limits

- The OpenTofu pages identify 1.12 where stated, and Helm command pages identify 4.2.2 where stated; other pages are rolling documentation.
- These sources do not establish repository versions, backend guarantees, provider behavior, cluster admission, live drift, production authority, or future apply results.
