---
name: build-tool-professional-usage
description: Use when Make, Bazel, Gradle, Maven, npm scripts, task runners, code generation, build cache, remote execution, artifact reproducibility, or CI build graph behavior needs professional evidence.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "131"
changeforge_version: 0.1.0
---

# Mission

Ensure build tools produce reproducible, declared, cache-correct artifacts through explicit inputs, outputs, dependencies, generator ownership, environment boundaries, and validation evidence. Treat a passing local build as insufficient when undeclared inputs, generated outputs, hidden environment, or cache behavior can make CI or release artifacts differ.

# When To Use

Use when a change touches Makefiles, Bazel, Buck, Pants, Gradle, Maven, npm/pnpm/yarn scripts, Turborepo, Nx, code generation, build cache, remote execution, hermeticity, artifact packaging, build environment variables, compiler/linker flags, generated source, CI build graph, monorepo task dependencies, or reproducible release artifacts.

# Do Not Use When

Do not use for a simple source-only code change where the existing build graph is not altered, for package dependency governance without build graph impact, or for shell-script safety that is better owned by `shell-cli-professional-usage`.

# Non-Negotiable Rules

- Every generated artifact has a declared source, generator, output path, committed/ignored policy, and drift check.
- Build actions must declare inputs and outputs. Undeclared includes, env vars, downloaded files, local absolute paths, timestamps, and network calls are cache correctness defects.
- CI build commands must match the repository's source of truth; local aliases are not evidence unless they call the same target.
- Remote cache and remote execution require stable action keys, pinned toolchains, deterministic outputs, and secret-free logs.
- Generated outputs and source specs move together unless repository policy says outputs are not committed.
- Build fixes must scan for the same pattern in sibling packages, targets, modules, or task pipelines.
- Build cache invalidation must include schema, generator, compiler, flags, lockfiles, and platform inputs.
- Do not hide build failures by broadening globs, disabling strict deps, or adding order-only dependencies without understanding why the graph was wrong.
- Release artifacts require reproducibility evidence: artifact path, checksum or digest, build command, environment, and provenance when available.
- Build tools must not write to source, HOME, or global caches during validation unless that behavior is declared and safe for the sandbox.

# Industry Benchmarks

Anchor decisions against Bazel hermeticity and strict dependency rules, Gradle configuration cache and build cache guidance, Maven reproducible-build practices, GNU Make dependency-file discipline, npm/pnpm/yarn frozen install behavior, SLSA provenance expectations, reproducible-builds.org principles, and monorepo affected-task graph practices used by Nx, Turborepo, Pants, and Buck.

# Selection Rules

Select when build graph, generated artifact, cache correctness, task orchestration, toolchain pinning, or artifact reproducibility is the central risk. Pair with `package-dependency-management` for dependency graph changes, `ci-cd` for pipeline wiring, `validation-broker` for changed-path-to-target mapping, and `agent-tool-permission-sandbox` for build commands that write generated outputs, caches, or release artifacts.

# Risk Escalation Rules

Escalate to `delivery-release-gate` when build output is shipped, published, containerized, signed, or used for deployment. Escalate to `security-privacy-gate` for supply-chain provenance, untrusted codegen plugins, secrets in build logs, or network downloads. Escalate to `architecture-impact-reviewer` when build graph boundaries reveal module dependency drift. Escalate to `quality-test-gate` when build target changes alter test selection or generated-contract validation.

# Critical Details

- **Declared dependency graph.** A target that compiles only because a dependency is transitively or hoisted into scope is broken even when local build passes.
- **Generated output ownership.** The generator source, tool version, config, and output policy determine whether a diff should be edited or regenerated.
- **Hermetic inputs.** Locale, timezone, current time, absolute path, username, HOME contents, network, and machine-specific files make action cache keys lie unless declared or removed.
- **Cache correctness.** Remote cache hit is not proof; compare action inputs, toolchain version, and output determinism when behavior changes.
- **Task graph invalidation.** Monorepo affected builds must include generated sources, schema changes, lockfiles, env configs, and package boundaries.
- **Artifact provenance.** Release builds should name build target, source ref, dependency lock, toolchain, environment, checksum, and signing/provenance status.

# Failure Modes

- **Bazel undeclared dependency:** target compiles locally because another target exports a transitive dep, then fails under strict deps or remote execution.
- **Generated artifact drift:** source schema changes but generated client is stale; consumers compile against old behavior.
- **Cache poisoning:** action reads an undeclared env var or file; cache returns output for the wrong config.
- **Non-reproducible package:** artifact embeds timestamp, absolute path, or host name; checksum changes across builds.
- **Hidden network fetch:** build downloads a tool at execution time, bypassing dependency review and offline CI.
- **Overbroad glob:** new files are silently included or excluded, changing artifact contents without review.
- **CI/local mismatch:** local `npm run build` differs from CI target; one passes while release target fails.
- **Task graph under-selection:** affected tests skip a package that consumes generated output.

# Output Contract

Return a Build Tool Usage Record with:

- `build_surface` (tool, target, task, generator, package, artifact)
- `graph_boundary` (declared inputs, outputs, dependencies, toolchain, environment)
- `generated_artifact_policy` (source, generator, output, committed/ignored, drift check)
- `cache_contract` (local/remote cache, action key inputs, invalidation sources, nondeterminism risks)
- `artifact_contract` (artifact path, checksum/digest, provenance/signing, reproducibility status)
- `decision_record` (change made, alternatives rejected, placement rationale)
- `validation_commands` (build, affected tests, codegen, cache/drift check, reproducibility check)
- `tool_permission_boundary` (read-only vs generated-output write vs cache/artifact write)
- `residual_risk` (unproven platform, remote cache, release artifact, generator, or downstream consumer)

# Quality Gate

1. Build inputs, outputs, dependencies, toolchain, and environment assumptions are declared.
2. Generated artifacts have source/generator/output policy and drift validation.
3. Cache keys include every behavior-affecting input or cache is disabled for nondeterministic steps.
4. CI and local validation target the same build behavior or differences are explained.
5. Monorepo affected-task graph includes generated and transitive consumers.
6. Release artifacts have command, path, digest, and provenance/signing status where relevant.
7. Tool permission boundary states generated-output, cache, artifact, HOME, and network behavior.
8. Residual risk names untested platform, remote execution, downstream package, or cache state.

# Used By

delivery-release-gate, architecture-impact-reviewer, quality-test-gate, ai-code-review-refactor, change-documentation-gate

# Handoff

Hand off to `package-dependency-management` for dependency graph and lockfile risk, `ci-cd` for pipeline execution, `delivery-release-gate` for release artifact rollout, `architecture-impact-reviewer` for module boundary drift, and `validation-broker` for affected-target selection.

# Completion Criteria

Build-tool work is complete when the build graph is declared, generated artifacts are governed, cache behavior is explainable, CI/local validation is aligned, release artifacts are reproducible enough for the risk class, and every unverified platform or cache boundary is named.
