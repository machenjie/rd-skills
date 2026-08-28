# IaC Source Contracts

Load for a named source, state, identity, or proposal decision. Terraform, OpenTofu, Pulumi, and CloudFormation are non-equivalent. Treat proposal evidence as non-authorizing unless separate production-mutation authority is confirmed.

Official pages were recorded as accessed on 2026-07-24.

## Tool Contracts And Sources

- **Terraform:** state/identity/locking, unknowns/targeting, import/move/lifecycle, recovery, and dependency locks.
  Sources:
    - [State purpose](https://developer.hashicorp.com/terraform/language/state/purpose)
    - [State locking](https://developer.hashicorp.com/terraform/language/state/locking)
    - [Plan](https://developer.hashicorp.com/terraform/cli/commands/plan)
    - [Expression references](https://developer.hashicorp.com/terraform/language/expressions/references)
    - [Import](https://developer.hashicorp.com/terraform/language/import)
    - [Moved blocks](https://developer.hashicorp.com/terraform/language/block/moved)
    - [Lifecycle](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)
    - [Dependency lock](https://developer.hashicorp.com/terraform/language/files/dependency-lock)
    - [State recovery](https://developer.hashicorp.com/terraform/cli/state/recover)
- **OpenTofu:** versioned plan/backend/lock/encryption/key recovery; do not infer Terraform equivalence.
  Sources:
    - [Plan](https://opentofu.org/docs/cli/commands/plan/)
    - [State locking](https://opentofu.org/docs/language/state/locking/)
    - [State backends](https://opentofu.org/docs/language/state/backends/)
    - [State encryption](https://opentofu.org/docs/language/state/encryption/)
    - [Dependency lock](https://opentofu.org/docs/language/files/dependency-lock/)
- **Pulumi:** backend/stack/refresh, identity/alias/protection/replacement, unknowns, and secret evidence.
  Sources:
    - [State and backends](https://www.pulumi.com/docs/reference/state/)
    - [Update plans](https://www.pulumi.com/docs/iac/operations/stack-management/update-plans/)
    - [Resource names](https://www.pulumi.com/docs/iac/concepts/resources/names/)
    - [Aliases](https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/)
    - [Protection](https://www.pulumi.com/docs/iac/concepts/resources/options/protect/)
    - [Secrets](https://www.pulumi.com/docs/iac/concepts/secrets/)
- **CloudFormation:** template/parameters, identity, change set/drift, policy/protection, and rollback recovery.
  Sources:
    - [Change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html)
    - [Drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html)
    - [Continue update rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html)
    - [Resource protection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html)
    - [Stack termination protection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html)

## Version Limit

Rolling sources do not prove current tool/provider/module/backend, target, experimental/regional behavior, or live state.

## Required Record

Return tool/version, target, source/state/lock/writer/identity, fresh proposal unknown/targeting limits, destructive/secret effects, recovery owner, and live-state/no-production limits.

## Professional Decision Rules

- Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target and versions.

## High-Value Gotchas

- Proposal evidence is neither execution authority nor convergence proof.
