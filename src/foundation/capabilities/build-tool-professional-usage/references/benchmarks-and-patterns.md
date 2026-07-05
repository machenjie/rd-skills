# Build Tool Benchmarks And Patterns

## Benchmarks

- Bazel hermeticity, strict deps, sandboxing, and remote execution guidance.
- Gradle build cache and configuration cache guidance.
- Maven reproducible-build practices and dependency mediation.
- GNU Make automatic dependency generation and order-only prerequisite guidance.
- npm, pnpm, and yarn frozen install and script reproducibility behavior.
- SLSA provenance and reproducible-builds.org principles.

## Pattern Matrix

| Build risk | Required pattern | Evidence |
| --- | --- | --- |
| Undeclared dependency | Strict deps or isolated package build | failing/passing target output |
| Generated output | Source/generator/output policy | codegen and drift check |
| Remote cache | Hermetic inputs and deterministic output | cache key input review |
| Artifact release | Reproducible command and digest | checksum/provenance record |
| Monorepo affected graph | Transitive generated consumers included | affected target list |
| Environment input | Pin or declare env var | config and command output |

## Code Generation

Generated output is professional only when the source authority, generator version, config, output location, committed/ignored policy, and validation command are named. A diff that changes generated output but not the source requires an explicit explanation.

## Cache Correctness

Cache correctness requires stable inputs, deterministic outputs, declared toolchains, and no hidden filesystem, network, time, or environment reads. Disable cache for steps that cannot meet that bar.
