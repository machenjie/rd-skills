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

Use when a change touches Makefiles, Ant, Bazel, Buck, Pants, Gradle, Maven, npm/pnpm/yarn scripts, Turborepo, Nx, code generation, build cache, remote execution, hermeticity, artifact packaging, build environment variables, compiler/linker flags, generated source declaration, CI build graph, monorepo task dependencies, or reproducible release artifacts.

# Do Not Use When

Do not use for a simple source-only code change where the existing build graph is not altered, for package dependency governance without build graph impact, or for shell-script safety that is better owned by `shell-cli-professional-usage`.

# Stage Fit

Use during planning, implementation, code-review, testing, release, and incident-repair stages when build graph, generated artifact, task-runner, cache, toolchain, or release artifact behavior can change correctness, reproducibility, test selection, or deployability. Re-enter after Makefile, BUILD, Gradle, Maven, npm/pnpm/yarn script, Nx/Turborepo/Pants/Buck, codegen config, lockfile, compiler flag, toolchain, CI target, cache, artifact packaging, or generated-output edits. Skip for source-only changes where the authoritative build graph, generated outputs, test-selection graph, caches, and release artifacts are unchanged.

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

Anchor decisions against Bazel hermeticity, sandboxing, and strict dependency rules; Gradle configuration cache and build cache guidance; Maven and Ant classpath/sourcepath behavior; GNU Make dependency-file, phony target, order-only prerequisite, and parallel execution discipline; npm/pnpm/yarn frozen install behavior; SLSA provenance expectations; reproducible-builds.org principles; and monorepo affected-task graph practices used by Nx, Turborepo, Pants, and Buck.

# Selection Rules

Select when build graph, generated artifact, cache correctness, task orchestration, toolchain pinning, or artifact reproducibility is the central risk. Pair with `package-dependency-management` for dependency graph changes, `ci-cd` for pipeline wiring, `validation-broker` for changed-path-to-target mapping, and `agent-tool-permission-sandbox` for build commands that write generated outputs, caches, or release artifacts.

# Risk Escalation Rules

Escalate to `delivery-release-gate` when build output is shipped, published, containerized, signed, or used for deployment. Escalate to `security-privacy-gate` for supply-chain provenance, untrusted codegen plugins, secrets in build logs, or network downloads. Escalate to `architecture-impact-reviewer` when build graph boundaries reveal module dependency drift. Escalate to `quality-test-gate` when build target changes alter test selection or generated-contract validation.

# Proactive Professional Triggers

- **Signal:** A build failure is "fixed" by changing only a local command, alias, glob, classpath, `PATH`, env var, or strict-deps flag. **Hidden risk:** the authoritative CI/release target still uses a different graph or hides an undeclared input. **Required professional action:** identify the source-of-truth target and compare local, CI, and release commands before accepting the fix. **Route to:** `ci-cd`, `validation-broker`. **Evidence required:** authoritative command, changed inputs/outputs, failing/passing target output, and mismatch or alignment note.
- **Signal:** Generated files, clients, schemas, protobuf/OpenAPI outputs, lockfiles, or compiled assets change without the source spec, generator config, or drift command. **Hidden risk:** generated output becomes the false source of truth and consumers compile stale behavior. **Required professional action:** establish source/generator/output policy and run or disclose drift validation. **Route to:** `data-format-contract-usage`, `contract-testing`. **Evidence required:** source spec, generator version/config, output path, committed/ignored decision, drift command output or not-run owner.
- **Signal:** Monorepo affected-test, task-cache, remote-cache, or build-cache behavior is trusted after changing generated inputs, package boundaries, lockfiles, env config, compiler flags, or toolchain versions. **Hidden risk:** graph under-selection or stale cache returns green evidence for untested consumers. **Required professional action:** verify task graph edges and cache-key inputs, then rerun without suspect cache when needed. **Route to:** `quality-test-gate`, `repository-graph-analysis`. **Evidence required:** affected target list, cache key inputs, generated/transitive consumers, cache bypass or invalidation result, and residual untested consumers.
- **Signal:** Build validation writes to source, `dist/`, HOME, global caches, package registries, or network resources without permission and sandbox classification. **Hidden risk:** validation mutates user state, pollutes caches, leaks secrets, or turns a read check into a release action. **Required professional action:** classify tool permission before execution and isolate or dry-run writes. **Route to:** `agent-tool-permission-sandbox`, `security-privacy-gate`. **Evidence required:** command class, write paths, network behavior, sandbox boundary, redaction rule, and rollback or cleanup path.
- **Signal:** Repository graph, project memory, previous CI logs, or old build artifacts are reused after build config, lockfile, generated source, toolchain, or task graph edits. **Hidden risk:** stale memory or graph evidence certifies the wrong build boundary. **Required professional action:** treat graph and memory as selectors, rerun selected source reads and build probes, and mark stale execution evidence rejected. **Route to:** `project-memory-governance`, `execution-trajectory-analysis`, `repository-graph-analysis`. **Evidence required:** accepted/rejected memory, graph freshness, changed paths, rerun validator command, exit code, and report/artifact path.

# Critical Details

- **Declared dependency graph.** A target that compiles only because a dependency is transitively or hoisted into scope is broken even when local build passes.
- **Generated output ownership.** The generator source, tool version, config, and output policy determine whether a diff should be edited or regenerated.
- **Hermetic inputs.** Locale, timezone, current time, absolute path, username, HOME contents, network, and machine-specific files make action cache keys lie unless declared or removed.
- **Cache correctness.** Remote cache hit is not proof; compare action inputs, toolchain version, and output determinism when behavior changes.
- **Task graph invalidation.** Monorepo affected builds must include generated sources, schema changes, lockfiles, env configs, and package boundaries.
- **Artifact provenance.** Release builds should name build target, source ref, dependency lock, toolchain, environment, checksum, and signing/provenance status.
- **Make parallel safety is explicit.** Parallel `make -j` requires correct prerequisites, no hidden shared temp files, phony targets marked `.PHONY`, and order-only dependencies used only for ordering, not missing inputs.
- **Bazel sandboxing exposes undeclared inputs.** Do not disable sandboxing or strict deps to pass CI; declare generated sources, tools, data files, and runtime dependencies in the owning target.
- **JVM classpath and sourcepath are contracts.** Ant, Maven, and Gradle fixes must name whether compile/test/runtime classpath or sourcepath changed and why transitive scope is not hiding a missing direct dependency.
- **Build rules write to outputs, not source.** A build action that writes into the source tree, HOME, or a global cache must be declared, isolated, or rejected unless the repository policy makes it authoritative.

# Failure Modes

- **Bazel undeclared dependency:** target compiles locally because another target exports a transitive dep, then fails under strict deps or remote execution.
- **Generated artifact drift:** source schema changes but generated client is stale; consumers compile against old behavior.
- **Cache poisoning:** action reads an undeclared env var or file; cache returns output for the wrong config.
- **Non-reproducible package:** artifact embeds timestamp, absolute path, or host name; checksum changes across builds.
- **Hidden network fetch:** build downloads a tool at execution time, bypassing dependency review and offline CI.
- **Overbroad glob:** new files are silently included or excluded, changing artifact contents without review.
- **CI/local mismatch:** local `npm run build` differs from CI target; one passes while release target fails.
- **Task graph under-selection:** affected tests skip a package that consumes generated output.

# Anti-Rationalization Table

| Rationalization | Hidden Risk | Required Correction |
|---|---|---|
| "Local build passed." | CI, remote execution, or release target uses different inputs. | Run the authoritative target or explain the mismatch. |
| "Just add the missing package to the classpath." | Transitive dependency or sourcepath leak remains hidden. | Declare the owning dependency in the correct target/scope. |
| "Generated code can be edited directly." | Source schema and generated output drift. | Regenerate from source or document checked-in output authority. |
| "Disable strict deps to unblock CI." | Undeclared dependency becomes permanent. | Fix the build graph and keep strict validation enabled. |
| "Remote cache hit proves correctness." | Cache key omitted a behavior-affecting input. | Verify declared inputs/toolchain and rerun without suspect cache when needed. |

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, risk, and output-contract rules.

Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete build-tool usage record, generated-artifact handoff, cache/test-selection review, or release artifact checklist.
Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) only when build graph semantics, generated-source policy, Make/Ant/Bazel/Maven/Gradle behavior, cache correctness, or artifact reproducibility needs deeper benchmark support.
Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs concrete build evidence, generated-drift proof, cache/provenance records, or CI/local comparison patterns.
Do not load references for source-only changes that do not alter build graph, generated outputs, cache keys, toolchains, or release artifacts.
References are just-in-time support, not default-loaded encyclopedia content.

# Output Contract

Return a Build Tool Usage Record with:

- `build_surface` (tool, target, task, generator, package, artifact; includes Ant, Make, Bazel, Gradle, Maven, and task runners where relevant)
- `graph_boundary` (declared inputs, outputs, dependencies, toolchain, environment)
- `make_contract` (parallel safety, `.PHONY` targets, order-only dependencies, shared temp/output risks)
- `jvm_classpath_contract` (classpath/sourcepath behavior for Ant/Maven/Gradle, direct vs transitive scope)
- `bazel_sandbox_contract` (sandboxing status, strict deps, generated source declaration, data/tool inputs)
- `generated_artifact_policy` (source, generator, output, committed/ignored, drift check)
- `write_boundary` (source tree vs output directory, HOME/global cache writes, sandbox/network policy)
- `cache_contract` (local/remote cache, action key inputs, invalidation sources, nondeterminism risks)
- `artifact_contract` (artifact path, checksum/digest, provenance/signing, reproducibility status)
- `decision_record` (change made, alternatives rejected, placement rationale)
- `validation_commands` (build, affected tests, codegen, cache/drift check, reproducibility check)
- `validation_freshness` (commands or validators rerun after the final material build/config/generated edit; stale output rejected or named)
- `what_evidence_proves` and `what_evidence_does_not_prove` (covered target, platform, cache mode, generated output, release artifact, and limits)
- `tool_permission_boundary` (read-only vs generated-output write vs cache/artifact write)
- `memory_graph_execution_record` (repository graph, project memory, previous log, or trajectory evidence accepted, rejected, stale, partial, or not used)
- `residual_risk` (unproven platform, remote cache, release artifact, generator, or downstream consumer)

# Evidence Contract

Close a build-tool record only when these answers are concrete: **boundaries inspected** across build files, task runner config, generated sources, lockfiles, toolchain, environment, cache, CI target, release artifact, and write paths; direct source/config/build-output evidence accepted or rejected; repository graph, project memory, old CI logs, generated artifacts, and execution trajectory used only as selectors unless rerun against current source; validation evidence names command/test/validator/report/artifact, output summary, exit code or not-run status, and freshness after the final material edit; what evidence proves and does not prove for platform, cache mode, remote execution, generated drift, downstream consumers, and release artifact reproducibility; reuse and placement rationale for new build targets, generators, scripts, outputs, or cache rules; behavior preservation, rollback or cleanup path, residual risk owner, and next gate.

# Quality Gate

1. Build inputs, outputs, dependencies, toolchain, and environment assumptions are declared.
2. Generated artifacts have source/generator/output policy and drift validation.
3. Make, Ant, Bazel, Maven, Gradle, and generated-source behavior names parallel safety, classpath/sourcepath, sandboxing, and write-boundary assumptions where relevant.
4. Cache keys include every behavior-affecting input or cache is disabled for nondeterministic steps.
5. CI and local validation target the same build behavior or differences are explained.
6. Monorepo affected-task graph includes generated and transitive consumers.
7. Release artifacts have command, path, digest, and provenance/signing status where relevant.
8. Tool permission boundary states generated-output, cache, artifact, HOME, and network behavior.
9. Validation covers at least the changed build/generator/cache/artifact path with command output, exit code, report/artifact, or a not-run disclosure.
10. Graph, memory, previous logs, and old artifacts are freshness-checked and cannot substitute for current source/build validation.
11. Residual risk names untested platform, remote execution, downstream package, release artifact, generator, or cache state.

# Used By

delivery-release-gate, architecture-impact-reviewer, quality-test-gate, ai-code-review-refactor, change-documentation-gate

# Handoff

Hand off to `package-dependency-management` for dependency graph and lockfile risk, `ci-cd` for pipeline execution, `delivery-release-gate` for release artifact rollout, `architecture-impact-reviewer` for module boundary drift, and `validation-broker` for affected-target selection.

# Completion Criteria

Build-tool work is complete when the build graph is declared, generated artifacts are governed, cache behavior is explainable, CI/local validation is aligned, release artifacts are reproducible enough for the risk class, and every unverified platform or cache boundary is named.
