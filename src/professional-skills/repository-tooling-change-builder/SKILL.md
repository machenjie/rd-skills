---
name: repository-tooling-change-builder
description: "Use `task-agent` for a bounded repository generator, plugin, harness, CLI, monorepo automation, or maintenance utility source change. Skip product behavior, config-only work, docs, release, review, and planning."
---

# repository-tooling-change-builder

## Role

Support `task-agent` in changing bounded repository tooling with authority, compatibility, determinism, cleanup, and proof.

## When To Use

- one bounded repository code generator, compiler plugin, linter, formatter, harness, internal CLI, build or monorepo automation, or maintenance utility change
- a direct task whose primary consumers are repository developers, tests, builds, or local automation

## Do Not Use

- backend service, product behavior, or business logic
- build-graph or build-configuration-only work with no repository-tool source change
- documentation-only work
- production mutation, deployment, release, or rollback
- independent review, task decomposition, planning, routing, or control

## Required Inputs

- behavior, scope, owner, consumer, invocation, tests, and outcomes
- source/generated authority, toolchain/host, effects, compatibility, cleanup, and rollback

## Professional Decision Rules

- Keep the tooling decision within its owner, inputs, stops, and output contract.
- Bind generated output and plugins to authoritative inputs, source ownership, destination, tool or host versions, compatibility, deterministic identity, and a non-circular clean-checkout bootstrap.
- Bind mutating commands and subprocesses to resolved targets and invocation contracts, with atomic completion or explicit recovery, cancellation and child cleanup, and safe rerun behavior.
- Prove the harness oracle with valid and invalid controls while keeping harness health distinct from the changed behavior's correctness.

## High-Value Gotchas

- Generated output can look correct while bootstrap order or source authority is wrong.
- A subprocess can report success before output, cleanup, or child completion is durable.
- A maintenance command can cross its intended workspace or mutate files on rerun.

## Execution Checklist

- **Task mode:** Map source authority, callers, generated outputs, side effects, and cleanup ownership.
- Reuse the existing command, generator, harness, or process boundary when it owns the behavior.
- Verify compatibility, deterministic output, atomic completion, and bounded rerun behavior.
- Record skipped hosts, toolchains, consumers, and recovery paths as proof limits.
- Minimal validation: run normal, invalid, boundary, rerun, and forbidden-effect tests.

## Stop / Escalation Conditions

- Return multiple owners, shared contracts, or ordered tasks to planning.
- Stop on unresolved authority, bootstrap, compatibility, oracle, recovery, or validation.
- Keep other work at its owner; do not claim review.

## Output Contract

- changed files, owner, consumer, reuse, placement, invocation, compatibility, authority, bootstrap, file/process, and failure decisions
- validation, negative controls, skips, diff, cleanup/rollback, proof limits, residual risk, and boundary handoffs

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [generator and plugin contracts](references/generator-and-plugin-contracts.md) | targeted | Generated authority, bootstrap, compiler protocol, host API, diagnostics, fixes, or version compatibility changes | No generator or compiler/linter/formatter plugin behavior changes | task-agent | boundary-decision, selected-approach, proof-limit |
| [harness validity contracts](references/harness-validity-contracts.md) | targeted | Test discovery, orchestration, oracle, fixtures, negative controls, benchmark measurement, or harness exit behavior changes | Existing unchanged harness directly proves the accepted behavior | task-agent | decision-record, validation-plan, proof-limit |
| [repository automation contracts](references/repository-automation-contracts.md) | targeted | Internal CLI, hook, monorepo automation, maintenance mutation, subprocess, rerun, or cleanup behavior changes | No repository automation interface or mutation changes | task-agent | decision-record, failure-decision, proof-limit |
