# IaC Source Contracts
Use this reference to identify the selected tool's source, state, identity, and preview evidence. Load capsule-named `infrastructure-as-code-safety` guidance for detailed safety decisions. Keep provider policy in the capsule-named cloud Domain Skill rather than this Professional reference.
Official pages in this reference were recorded as accessed on 2026-07-24.
## Terraform
- Inspect configuration, state mapping, backend locking support, provider locks, and the final plan separately.
- Treat unknown values and targeted plans as explicit proof limits.
- Use import or moved declarations only with verified remote identity and lifecycle effects.
- Do not describe state recovery as reversal of remote changes.
Primary sources:
- [State purpose and mapping](https://developer.hashicorp.com/terraform/language/state/purpose)
- [State locking](https://developer.hashicorp.com/terraform/language/state/locking)
- [Plan modes and targeting](https://developer.hashicorp.com/terraform/cli/commands/plan)
- [Unknown values](https://developer.hashicorp.com/terraform/language/expressions/references)
- [Import](https://developer.hashicorp.com/terraform/language/import)
- [Moved blocks](https://developer.hashicorp.com/terraform/language/block/moved)
- [Lifecycle meta-argument](https://developer.hashicorp.com/terraform/language/meta-arguments/lifecycle)
- [Dependency lock file](https://developer.hashicorp.com/terraform/language/files/dependency-lock)
- [State recovery](https://developer.hashicorp.com/terraform/cli/state/recover)
Version limit: pages can follow the current Terraform release. They do not establish the repository's CLI, provider, backend, module, or remote-system behavior.
## OpenTofu
- Verify backend locking and state format for the selected OpenTofu version.
- Treat encrypted state and plan compatibility as a key-lifecycle decision.
- Do not project OpenTofu encryption or experimental behavior onto Terraform.
Primary sources:
- [Plan and targeting](https://opentofu.org/docs/cli/commands/plan/)
- [State locking](https://opentofu.org/docs/language/state/locking/)
- [State backends](https://opentofu.org/docs/language/state/backends/)
- [State and plan encryption](https://opentofu.org/docs/language/state/encryption/)
- [Dependency lock file](https://opentofu.org/docs/language/files/dependency-lock/)
Version limit: the recorded pages identify OpenTofu 1.12 where stated. Check
feature maturity, migration compatibility, backend support, and key recovery.
## Pulumi
- Inspect the selected backend, stack state, refresh stance, aliases, protection, and replacement order.
- Treat an update plan as non-transactional and incomplete where values remain unknown.
- Keep secret-bearing state and callbacks outside visible evidence.
Primary sources:
- [State and backends](https://www.pulumi.com/docs/reference/state/)
- [Update plans](https://www.pulumi.com/docs/iac/operations/stack-management/update-plans/)
- [Resource names and identity](https://www.pulumi.com/docs/iac/concepts/resources/names/)
- [Aliases](https://www.pulumi.com/docs/iac/concepts/resources/options/aliases/)
- [Resource protection](https://www.pulumi.com/docs/iac/concepts/resources/options/protect/)
- [Secrets](https://www.pulumi.com/docs/iac/concepts/secrets/)
Version limit: backend guarantees, provider behavior, update-plan format, and
resource options vary by Pulumi and provider version.
## AWS CloudFormation
- Inspect template, parameters, logical and physical identity, stack policy, termination protection, and change set separately.
- Treat a change set as a proposal that can still fail during execution.
- Record unsupported drift fields and failed-rollback recovery as proof limits.
Primary sources:
- [Change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-changesets.html)
- [Drift-aware change sets](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/drift-aware-change-sets.html)
- [Continue update rollback](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-updating-stacks-continueupdaterollback.html)
- [Stack policies](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/protect-stack-resources.html)
- [Termination protection](https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/using-cfn-protect-stacks.html)
Version limit: resource coverage, replacement behavior, quotas, custom resources,
and rollback outcomes are service, region, account, and template specific.
## Required Record
Return the tool and version, exact target, source and state owner, identity mapping,
fresh preview evidence, destructive or sensitive effects, recovery owner, and
explicit limits on live-state and execution claims.
