# IaC Source Contracts

Load for a named source, state, identity, or proposal decision. Terraform, OpenTofu, Pulumi, and CloudFormation are non-equivalent. Treat proposal evidence as non-authorizing unless separate production-mutation authority is confirmed.

Official pages were recorded as accessed on 2026-07-24.

## Tool Contracts And Sources

- **Terraform:** state/identity/locking, unknowns/targeting, import/move/lifecycle, recovery, and dependency locks.
  Sources: https://developer.hashicorp.com/terraform/language/state/purpose https://developer.hashicorp.com/terraform/language/state/locking https://developer.hashicorp.com/terraform/cli/commands/plan https://developer.hashicorp.com/terraform/language/expressions/references https://developer.hashicorp.com/terraform/language/import https://developer.hashicorp.com/terraform/language/block/moved https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle https://developer.hashicorp.com/terraform/language/files/dependency-lock https://developer.hashicorp.com/terraform/cli/state/recover
- **OpenTofu:** versioned plan/backend/lock/encryption/key recovery; do not infer Terraform equivalence.
  Sources: https://opentofu.org/docs/cli/commands/plan/ https://opentofu.org/docs/language/state/locking/ https://opentofu.org/docs/language/state/backends/ https://opentofu.org/docs/language/state/encryption/ https://opentofu.org/docs/language/files/dependency-lock/
- **Pulumi:** backend/stack/refresh, identity/alias/protection/replacement, unknowns, and secret evidence.
  Sources: https://www.pulumi.com/docs/reference/state/ https://www.pulumi.com/docs/iac/operations/stack-management/update-plans/ https://www.pulumi.com/docs/iac/concepts/resources/names/ https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/ https://www.pulumi.com/docs/iac/concepts/resources/options/protect/ https://www.pulumi.com/docs/iac/concepts/secrets/
- **CloudFormation:** template/parameters, identity, change set/drift, policy/protection, and rollback recovery.
  Sources: https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html

## Version Limit

Rolling sources do not prove current tool/provider/module/backend, target, experimental/regional behavior, or live state.

## Required Record

Return tool/version, target, source/state/lock/writer/identity, fresh proposal unknown/targeting limits, destructive/secret effects, recovery owner, and live-state/no-production limits.

## Professional Decision Rules

- Separate state layers; change the smallest owner; bind secret-free non-mutating proposal evidence to target and versions.

## High-Value Gotchas

- Proposal evidence is neither execution authority nor convergence proof.
