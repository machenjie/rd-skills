---
name: library-tool-product-builder
description: "Use `task-agent` for distributed libraries, SDK internals, public CLIs, and developer tools with fixed public contracts. Skip repository-only tools, services, contract changes, and production release decisions."
---

# Library and Tool Product Builder

## Role

Support `task-agent` in implementing independently distributed library and tool behavior through its published artifact and external consumer.

## When To Use

- Library algorithms, SDK internals, public CLI features, and developer tool defects.
- Resource or lifecycle repairs that preserve the agreed public contract.

## Do Not Use

- Repository-only generators, plugins, harnesses, or automation.
- Services, workers, native runtimes, or firmware.
- Public API, cancellation, compatibility, or schema contract changes.
- Production release, promotion, or rollback decisions.

## Required Inputs

- Consumer-visible behavior, fixed public contract, and supported environments.
- Source entrypoints, package artifact, external consumer, and acceptance.

## Professional Decision Rules

- Trace the defect from the consumer entrypoint through algorithm, state, and resource ownership.
- Preserve public values, errors, cancellation, and lifecycle semantics under the agreed contract.
- Keep packaging metadata, exports, dependencies, and runtime files consistent with the built artifact.
- Exercise the artifact from a minimal external consumer outside the source tree.
- Distinguish source tests, package validity, and consumer behavior as separate evidence.

## High-Value Gotchas

- Source imports can hide missing files, invalid exports, or undeclared dependencies in the package.
- Internal cleanup changes can alter externally observable cancellation or error behavior.
- A CLI exit code can hide unfinished children or partial output.

## Execution Checklist

1. Establish the consumer failure and fixed compatibility boundary.
2. Repair the owning source and test the mechanism.
3. Build the package with the repository's supported toolchain.
4. Install or load that artifact in an isolated minimal consumer.
5. Verify the requested behavior and applicable failure cleanup.

## Stop / Escalation Conditions

- Resolve public contract changes before implementing them.
- Report unsupported consumers or environments as explicit proof limits.

## Output Contract

- Source and artifact changes with compatibility and lifecycle decisions.
- Source tests, package identity, and external consumer results.
- Cleanup, recovery, unverified environments, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [artifact consumer verification](references/artifact-consumer-verification.md) | targeted | A library SDK CLI or tool change needs artifact and external consumer proof | No library or tool product behavior is being changed | task-agent | decision-record, validation-plan, proof-limit |
