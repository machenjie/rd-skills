---
name: repository-tooling-change-builder
description: "Use `task-agent` for repository tools, development workspace/build/dependency changes, or Git collaboration. Keep product behavior, infrastructure, and production release decisions with their owners."
---

# Repository Tooling Change Builder

## Role

Support `task-agent` in implementing repository tooling, reproducible development workspaces, and bounded Git collaboration.

## When To Use

- Tool source: generators, compiler plugins, harnesses, internal CLIs, and automation.
- Workspace/build: bootstrap, toolchains, build graphs, dependencies, and CI compilation configuration.
- Git collaboration: branches, rebase, conflicts, and authorized history recovery.

## Do Not Use

- Product behavior, cloud resources, or runner infrastructure.
- Production release, promotion, or rollback decisions.
- An incidental build or Git operation inside an already owned feature task.

## Required Inputs

- Selected mode, requested outcome, repository state, and affected consumers.
- Source, generated-output, and lockfile authority.
- Authorized mutation, recovery boundary, and observable acceptance.

## Professional Decision Rules

- Bind generated output to authoritative source, tool versions, and reproducible bootstrap order.
- Compare actual build inputs and resolved dependencies when local and CI results differ.
- Preserve user work before Git mutation; resolve semantic conflicts at their source owner.
- Keep subprocess completion, cancellation, cleanup, and rerun behavior explicit.
- Prove harness oracles with valid and invalid controls.

## High-Value Gotchas

- Successful local compilation can hide undeclared inputs or stale generated output.
- A command can exit before its children finish or output becomes durable.
- A clean merge can preserve syntax while changing behavior.

## Execution Checklist

1. Confirm the mode, source authority, consumers, and mutation boundary.
2. Reuse the owning command, generator, build graph, or Git operation.
3. Apply the smallest coherent change with a recoverable checkpoint.
4. Validate the changed behavior and relevant clean-checkout or rerun path.

## Stop / Escalation Conditions

- Resolve unknown ownership, destructive authority, bootstrap order, or recovery before the affected mutation.
- Hand off newly discovered product, infrastructure, or production release decisions.

## Output Contract

- Changed files, mode, source authority, consumer, and compatibility decisions.
- Validation outcomes, recovery path, untested environments, and residual risk.

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [generator and plugin contracts](references/generator-and-plugin-contracts.md) | targeted | Generated authority, bootstrap, compiler protocol, host API, diagnostics, fixes, or version compatibility changes | No generator or compiler/linter/formatter plugin behavior changes | task-agent | boundary-decision, selected-approach, proof-limit |
| [harness validity contracts](references/harness-validity-contracts.md) | targeted | Test discovery, orchestration, oracle, fixtures, negative controls, benchmark measurement, or harness exit behavior changes | Existing unchanged harness directly proves the accepted behavior | task-agent | decision-record, validation-plan, proof-limit |
| [repository automation contracts](references/repository-automation-contracts.md) | targeted | Internal CLI, hook, monorepo automation, maintenance mutation, subprocess, rerun, or cleanup behavior changes | No repository automation interface or mutation changes | task-agent | decision-record, failure-decision, proof-limit |
| [workspace build and git modes](references/workspace-build-and-git-modes.md) | targeted | Bootstrap toolchain build dependency or Git state needs implementation | Only repository tool source changes under unchanged workspace and Git contracts | task-agent | decision-record, validation-plan, proof-limit |
