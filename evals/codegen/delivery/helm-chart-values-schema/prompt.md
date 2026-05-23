# Benchmark Prompt

## Task

Implement a focused change that turns an unsafe Helm chart release into a validated chart release path with typed values, secret sourcing, and atomic upgrade evidence.

## Context

The starter repo represents a Kubernetes service chart where production values currently carry credential-like fields and the release process relies on manual review. The implementation should keep the chart small while making the important delivery and security checks executable.

## Requirements

- Add `values.schema.json` coverage for required values, types, enums, resource shapes, and unsafe defaults.
- Remove plaintext API tokens, passwords, private keys, and credential-like values from production values.
- Require Helm lint, template rendering for each environment values file, rendered manifest validation, and policy checks before release.
- Document an atomic waited production upgrade path and a rollback scope that excludes CRDs, database changes, cloud resources, and secret rotation.

## Constraints

- Preserve chart version and `appVersion` as explicit release evidence.
- Keep chart dependencies reproducible through locked dependency metadata.
- Do not replace the benchmark with documentation-only output.
- Avoid any network dependency; scripts must run locally from the starter repo.

## Deliverables

- Source changes in the starter repo that implement the requested Helm chart behavior.
- Tests or executable checks that prove the required behavior and rejection paths.
- A short implementation note describing release tradeoffs and residual risk.

## Completion Evidence

- `bash setup.sh`
- `bash ../test-suite/run.sh`
- `bash ../security-checks/run.sh`
- Review evidence that no automatic failure condition applies.
