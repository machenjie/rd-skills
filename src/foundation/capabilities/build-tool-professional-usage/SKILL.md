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

Define build graph edges, source/generated authority, behavior inputs, toolchain identity, cache and parallel correctness, reproducibility, and evidence. Exclude package resolution and hosted pipelines.

## High-Value Rules

- **Own build-graph decisions and proof.** This capability decides and proves graph edges, generated authority, cache/action identity, and affected-test selection, then hands accepted constraints to `architecture-enforcement-tooling` for diagnostics, exceptions, baselines, and gates.
- **Model the target graph from real inputs and outputs.** Name source, generated, configuration, schema, environment, toolchain, and dependency edges needed to rebuild each affected artifact.
- **Declare source and generated authority.** Bind output to its generator, inputs, destination, repository policy, drift check, and sole editable authority.
- **Include behavior-affecting inputs in identity.** Define cache and incremental keys from the toolchain, flags, environment, platform, schemas, plugins, generated inputs, and transitive dependencies that can change behavior.
- **Prove parallel and incremental correctness.** Remove hidden ordering, undeclared files, shared mutable outputs, timestamp assumptions, and accidental working-directory state through clean, repeated, and concurrent builds.
- **Bound environment dependence.** Identify network, credentials, locale, clock, filesystem case, executable metadata, host tools, and platform assumptions, then make accepted dependencies explicit and reproducible.
- **Compare artifacts, not command success alone.** Tie source revision and build inputs to expected outputs, checksums or semantic comparison, packaged contents, and consumer-visible behavior.
- **Test failure and recovery paths.** Exercise missing input, stale generated output, cache miss or corruption, partial output, interrupted build, and clean rebuild relevant to the changed graph.

## Anti-Patterns

- Rely on command order, undeclared files, local caches, host-installed tools, or mutable shared output for a green build.
- Hand-edit generated artifacts or accept broad regeneration churn without source-to-output explanation.
- Treat local command success as proof of hosted enforcement, cross-platform reproducibility, or deployed artifact identity.

## Stop Conditions

Escalate unknown source authority, undeclared graph or cache inputs, irreproducible or racing output, unexpected network credentials, or unproved artifact equivalence.

## Output Contract

- build decision with graph edges, source and generated authority, input and toolchain identity, cache and parallel correctness, artifact comparison, failure evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Tool graph, generation, cache, or hermeticity mechanisms require comparison | The authoritative build target and mechanism are already fixed | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Build changes affect inputs, outputs, generators, caches, or consumers | Only source code changes under an unchanged build graph | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Build reproducibility depends on fresh commands, artifacts, or provenance | No graph, cache, or artifact claim requires proof | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
