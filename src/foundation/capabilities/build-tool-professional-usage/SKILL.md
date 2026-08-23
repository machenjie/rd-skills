---
name: build-tool-professional-usage
description: "`analysis-agent`/`task-agent`/`review-agent`: use when build graphs, codegen, caches, toolchains, or artifact reproducibility change; skip when build behavior is unaffected."
---

# build-tool-professional-usage

## Registry Trigger

**Use when**

- Makefile make Ant Bazel Buck Pants Gradle Maven npm script pnpm yarn Turborepo Nx build graph generated artifact codegen strict deps remote cache remote execution hermetic build
- undeclared dependency, generated source, generated source declaration, generator output source of truth, reproducible artifact, checksum, digest, build cache, action key, toolchain pin, local CI mismatch, make parallel, phony target, order-only dependency, bazel sandbox, classpath, sourcepath, output directory

**Do not use when**

- no task-local build tool professional usage decision is required

## Skill Role

Define build graph, source/generated authority, inputs, toolchain identity, cache/parallel correctness, reproducibility, and evidence; exclude packages and hosted pipelines.

## High-Value Rules

- Define graph, generated authority, cache/action identity, and affected-test proof.
- Route enforcement constraints to `architecture-enforcement-tooling`.
- Define inputs, outputs, dependencies, generated policy, toolchain, and cache identity.
- Prove clean, incremental, parallel, and hermetic behavior.
- Bound environment dependence.
- Compare source-bound artifacts rather than command success.
- Validate missing, stale, corrupt, partial, interrupted, and clean rebuild outcomes.

## Anti-Patterns

- Local success substituted for evidence of the build tool professional usage contract.

## Stop Conditions

Escalate unknown authority/inputs, racing or irreproducible output, unexpected network credentials, or unproved artifacts.

## Output Contract

- build decision with graph edges, source and generated authority, input and toolchain identity, cache and parallel correctness, artifact comparison, failure evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Tool graph, generation, cache, or hermeticity mechanisms require comparison | The authoritative build target and mechanism are already fixed | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Build changes affect inputs, outputs, generators, caches, or consumers | Only source code changes under an unchanged build graph | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Build reproducibility depends on fresh commands, artifacts, or provenance | No graph, cache, or artifact claim requires proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
