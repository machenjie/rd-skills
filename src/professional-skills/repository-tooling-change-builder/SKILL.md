---
name: repository-tooling-change-builder
description: "Use `task-agent` for a bounded repository generator, plugin, harness, CLI, monorepo automation, or maintenance utility source change. Skip product behavior, config-only work, docs, release, review, and planning."
---

# repository-tooling-change-builder

## Role

Support `task-agent` in changing repository tooling while preserving authority, compatibility, deterministic behavior, cleanup, and proof.

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

- accepted behavior, non-goals, edit scope, owner, minimum consumer, invocation, and tests
- source/generated authority, inputs, outputs, toolchain, host versions, and bootstrap
- file/process effects, compatibility, cleanup, rollback, and observable outcome signals

## Professional Decision Rules

- Inspect the owner, minimum consumer, tests, adjacent utilities, and reuse before adding structure.
- Bind generated output to authoritative inputs, generator version, destination, drift check, sole editable source, and a non-circular clean-checkout bootstrap.
- Bind plugins to supported host APIs and versions, including diagnostic identity, option schema, fix safety, rejection behavior, and real host integration.
- Prove harness oracle and regression mechanism with positive and negative controls. Keep harness health distinct from changed-product correctness.
- Preserve internal CLI argv, environment, working directory, stdio, exit, cancellation, rerun, and cleanup. Give multi-file output an explicit complete-or-recover contract.
- Declare behavior-affecting files, tools, locale, clock, randomness, network, credentials, executables, and platform facts. Reject ambient workstation or cache state as proof.
- Validate the mechanism through regeneration comparison, version-matched integration, negative controls, or CLI failure and cleanup paths.
- Stay within the accepted owner; do not widen public APIs or refactor unrelated tooling for tests.

## High-Value Gotchas

- Generated output drifts because the editable authority or regeneration check is ambiguous.
- A generator depends circularly on artifacts that only that generator can produce.
- A crash or failed subprocess leaves partial output that later appears current.
- Ambient tools, locale, time, network, credentials, or working directory make the result non-hermetic.
- A plugin passes unit tests but fails against a supported host API or version.
- A harness stays green after its target defect is reintroduced, creating false confidence.

## Execution Checklist

1. Inspect owner, consumer, invocation, tests, generated surfaces, versions, and reuse.
2. Map normal, invalid, interrupted, bootstrap, version-skew, rerun, and forbidden outcomes.
3. Implement the smallest complete source and proving-test change under one batch method.
4. Validate after the latest edit and inspect source plus generated diffs.
5. Report skipped checks, cleanup, compatibility limits, and residual ownership.

## Companion Boundary

- Load `build-tool-professional-usage` when graph edges, generated authority, cache identity, or reproducibility changes.
- Load `filesystem-process-safety` when local file commit, path containment, direct subprocess, timeout, cancellation, or cleanup changes.
- Load `targeted-validation-selection` only after proof strategy exists and exact repository-defined commands or coverage remain unresolved.

## Stop / Escalation Conditions

- Return a planning boundary for multiple owners, shared contracts, or ordered tasks.
- Stop when authority, ownership, bootstrap, compatibility, oracle, partial-write recovery, or validation remains unresolved.
- Stop build-only, product, docs-only, production, release, rollback, review, and control work at its boundary.
- Do not perform or claim independent review.

## Output Contract

- changed files, owner, consumer, reuse, placement, invocation, and compatibility
- authority, bootstrap, plugin, harness, hermeticity, file/process, and failure decisions
- fresh validation, negative controls, skipped checks, and final diff evidence
- cleanup, rollback, proof limits, residual risk, and planning or release boundary

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [generator and plugin contracts](references/generator-and-plugin-contracts.md) | targeted | Generated authority, bootstrap, compiler protocol, host API, diagnostics, fixes, or version compatibility changes | No generator or compiler/linter/formatter plugin behavior changes | task-agent | boundary-decision, selected-approach, proof-limit |
| [harness validity contracts](references/harness-validity-contracts.md) | targeted | Test discovery, orchestration, oracle, fixtures, negative controls, benchmark measurement, or harness exit behavior changes | Existing unchanged harness directly proves the accepted behavior | task-agent | decision-record, validation-plan, proof-limit |
| [repository automation contracts](references/repository-automation-contracts.md) | targeted | Internal CLI, hook, monorepo automation, maintenance mutation, subprocess, rerun, or cleanup behavior changes | No repository automation interface or mutation changes | task-agent | decision-record, failure-decision, proof-limit |
