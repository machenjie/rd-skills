# SDK Library Contract Design Benchmarks And Patterns

Use this reference when an SDK/library change needs benchmark-backed judgment, graph-memory-execution coupling, or release evidence beyond the compact `SKILL.md` checklist.

## Benchmark Anchors

- Version policy: Semantic Versioning 2.0.0, Cargo SemVer compatibility, Haskell PVP, ecosystem-specific pre-1.0 break policy, and date-based service API versioning when SDKs mirror server APIs.
- Change record: Keep a Changelog 1.1.0 with breaking, deprecated, removed, fixed, security, and migration entries tied to the package version.
- Public API diffing: `@microsoft/api-extractor`, `cargo semver-checks`, `revapi`, `japicmp`, Go `apidiff`, .NET `ApiCompat`, Python `griffe check`, `pyright --outputjson`, or the nearest ecosystem equivalent.
- Generated-client reproducibility: source spec hash, generator version or container digest, generator config, committed generated output, reviewed generated diff, and deterministic regeneration command.
- Supply chain: signed tags/commits where policy requires them, signed artifacts, npm provenance, PyPI Trusted Publishers/attestations, Maven/NuGet/crates/Go registry norms, SBOM, OSV scan, SLSA provenance, and registry-specific yank/hotfix path.
- Consumer proof: Pact or equivalent contract tests, old/new fixture-consumer builds, downstream smoke matrix, packed-artifact examples, runtime floor matrix, and generated signature snapshots.

## Contract Surface Matrix

| Surface | Evidence | Common Hidden Risk |
| --- | --- | --- |
| Exported symbols and public types | API diff, shipped/unshipped public API file, type snapshot | Minor release contains breaking rename, narrowing, abstract method, or enum change. |
| Generated operations and models | Spec hash, generator pin, generated diff review | Floating generator or template silently reshapes clients. |
| Error taxonomy | Throwable/error snapshot and negative contract tests | Downstream `instanceof`, code, or retry handling misses new or renamed errors. |
| Runtime and dependency floors | package metadata diff, runtime/package-manager matrix | Minor release breaks install for still-supported consumers. |
| Examples and docs | packed-artifact example run and versioned docs build | README compiles against source or stale docs instead of release artifact. |
| Publication artifacts | digest, signature, provenance, SBOM, registry metadata | Artifact cannot be verified, yanked, or hotfixed after publish. |

## Graph Memory Execution Coupling

- Repository graph: inspect exports, package manifests, generated trees, examples, docs, changelog, release scripts, test fixtures, and package dependency edges before classifying the change.
- Project memory: compare previous compatibility promises, accepted exceptions, deprecation windows, runtime floors, and consumer commitments with the current source; mark stale memory as not verified.
- Consumer graph: identify first-party consumers, fixture projects, generated-client users, public/private export boundaries, and downstream smoke targets; record unknown external consumers as residual risk.
- Execution trajectory: connect each observed change to the command or review artifact that proves it: API diff, generator command, packed example run, fixture build, contract test, matrix job, SBOM/provenance verification, or explicit not-verified owner.

## Compatibility Review Patterns

- Patch: bug fix only; no public type, generated shape, runtime floor, error taxonomy, default, package metadata, or dependency-floor break.
- Minor: additive surface that old consumers can ignore; examples, docs, changelog, and fixture consumers still pass.
- Major: removal, rename, required parameter, narrowed type, changed default, module-format flip, runtime-floor raise, error taxonomy break, or changed extension contract.
- Internal-only: no published package, exported symbol, generated client, docs example, fixture consumer, or package metadata boundary changes; prove with repository graph evidence.

## Handoff Boundaries

- Hand server API semantics to `api-contract-design`; keep SDK contract focus on generated clients, package surface, examples, and consumer compatibility.
- Hand mixed-version rollout windows to `version-compatibility`; keep SDK release classification tied to package versions and consumer adoption.
- Hand dependency/CVE/license/provenance depth to `package-dependency-management` and `security-privacy-gate`; keep this capability focused on publication evidence and rollback/yank behavior.
- Hand test depth and stale validation decisions to `quality-test-gate` and `validation-broker`; this capability names the required evidence but does not replace the validator.
