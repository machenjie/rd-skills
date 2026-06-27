---
name: sdk-library-contract-design
description: Designs SDK and library contracts with semver, generated clients, compatibility, deprecation, package publication, examples, consumer tests, documentation, and migration guarantees.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "97"
changeforge_version: 0.1.0
---

# Mission

Design public or internal SDK and library contracts that consumers can adopt safely across versions, package managers, generated clients, examples, deprecations, and migration windows.

# Pinned Tooling Baseline

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- Versioning: Semantic Versioning 2.0.0 for libraries; Cargo SemVer compatibility rules for Rust; PVP for Haskell; pre-1.0 packages must still document breaking change policy.
- Public-surface diffing: TypeScript `@microsoft/api-extractor` ≥ 7 + `api-documenter`; Rust `cargo semver-checks` ≥ 0.32 and `cargo public-api`; Java `revapi` or `japicmp` (Maven plugin); Go `golang.org/x/exp/cmd/apidiff`; .NET `Microsoft.DotNet.ApiCompat`; Python `griffe check` or `pyright --outputjson` baseline diff.
- Generated clients: OpenAPI Generator ≥ 7.x pinned, or Microsoft Kiota ≥ 1.x, or `protoc` ≥ 25 + language plugins, or `oapi-codegen` (Go) ≥ 2.x. Pin generator container digest, source spec hash, and generator config; commit generated output and review diff.
- Publication: npm with provenance (`npm publish --provenance` ≥ npm 9.5), PyPI with Trusted Publishers (OIDC) and `attestations`, Maven Central via Sonatype OSSRH with PGP signing, NuGet with `--skip-duplicate` and `dotnet nuget sign`, crates.io with `cargo publish --token` from OIDC, Go module proxy + `GOSUMDB`, GitHub Releases with attached SBOM (SPDX or CycloneDX).
- Compatibility tests: consumer-driven contract tests via Pact ≥ 4 for HTTP/gRPC; downstream smoke matrix in CI for top N consumers; snapshot tests of generated client signatures.
- Documentation generation: TypeDoc, Sphinx + `autodoc`, Javadoc / Dokka, rustdoc, `godoc`, DocFX; render to versioned doc site (Docusaurus / mkdocs / Hugo); maintain CHANGELOG in Keep a Changelog format.
- Supply-chain: SLSA Level ≥ 3 build provenance, `sigstore` / `cosign` for artifact signing, OSV scanner in CI, SBOM attached to every release.
- Runtime floors: declare in package metadata (`engines.node`, `python_requires`, `rust-version`, Maven `maven.compiler.release`, .NET `TargetFramework`); never silently raise the floor in a minor release.

# When To Use

Use this capability when a change adds, removes, publishes, regenerates, versions, or changes an SDK, client library, shared package, framework adapter, plugin API, generated client, public type surface, internal reusable library, sample project, or consumer-facing package documentation.

Also use it when repository graph, project memory, or execution traces show that exported types, generated output, package metadata, examples, deprecations, runtime floors, or consumer fixtures changed without matching compatibility and validation evidence.

# Do Not Use When

Do not use this capability for application-only code with no reusable contract. Do not use it instead of `api-contract-design` for server behavior, `version-compatibility` for mixed-version rollout, `package-dependency-management` for dependency graph risk, or language professional usage capabilities for runtime-specific idioms.

# Stage Fit

- **Planning / design:** define the contract surface, compatibility promise, version class, consumer inventory, generator source, runtime floors, and deprecation/migration path before coding.
- **Bug-fix / debugging / repair:** reproduce the consumer breakage, identify the contract drift, scan sibling exports/generated files/examples, and repair compatibility evidence with the code change.
- **Coding / implementation:** update exported APIs, generated clients, package metadata, docs, examples, and compatibility tests together.
- **Code-review / refactoring:** reject public-surface, runtime-floor, package-metadata, generated-output, or error-taxonomy changes without diff evidence and consumer validation.
- **Testing / release / handoff:** verify packaging, signatures/provenance, SBOM, changelog, migration guide, examples, downstream smoke tests, rollback/yank path, and residual risk owner before publish.

# Non-Negotiable Rules

- Define the supported contract surface explicitly before edit: exported symbols, public types, configuration keys, generated client operations, error types, lifecycle hooks, callbacks, extension points, default values, and required peer dependencies.
- Classify every change as patch, minor, major, or internal-only with written justification; tool-enforced via API-diff in CI; missing or wrong classification blocks release.
- Keep generated clients reproducible from a pinned source spec hash + pinned generator version; commit generated output; reviewer must inspect the generated diff.
- Provide a CHANGELOG entry (Keep a Changelog format) and a migration note for every removal, rename, default change, behavioral change, error-shape change, generated-code change, runtime-floor change, and dependency-floor change.
- Deprecation precedes removal: mark deprecated in a minor release, document replacement and removal version, emit a runtime warning when feasible, keep the deprecated surface working until the next major.
- Maintain runnable examples for the primary flow, auth/config, pagination or streaming if applicable, and at least one error path; examples run in CI against the packed artifact, not source.
- Publish through a reproducible release pipeline with: signed commits/tags, signed artifacts (sigstore / GPG), provenance attestation (SLSA), SBOM, automated CHANGELOG, and a documented yank/rollback path.
- Validate consumer compatibility before release via API-diff, snapshot tests, contract tests, fixture-consumer build, and downstream smoke matrix.
- Never raise the minimum runtime (`engines.node`, `python_requires`, `rust-version`, Java release target, .NET TFM) in a minor or patch release.
- Public types are part of the contract: changing a parameter from required to optional, narrowing a union, removing a generic constraint, or adding an abstract method is a breaking change.
- Error types and exception hierarchies are part of the contract; renaming an exception class is breaking.
- Default values are part of the contract; flipping a default behavior is breaking.
- SDK/library claims must cite **repository evidence** (exports, package metadata, generated files, examples, docs, consumers), **memory evidence** (prior compatibility and deprecation decisions accepted or updated), **graph evidence** (downstream consumer and package dependency edges), and **execution evidence** (API diff, fixture build, packed-artifact example run, contract/smoke tests).

# Industry Benchmarks

Anchor decisions in SemVer 2.0.0, Keep a Changelog 1.1.0, Cargo SemVer, npm/PyPI/Maven/NuGet/crates/Go provenance norms, SLSA, OpenSSF, Pact, Microsoft ApiCompat/PublicAPI analyzers, Eclipse PDE API Tools, Stripe/Google SDK release practices, and OWASP SCVS. Keep the body focused on routing and evidence; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for benchmark details, surface matrices, and coupling patterns.

# Selection Rules

Select this capability when the primary risk is a reusable client or library contract that other code depends on. Pair with `api-contract-design` when the SDK mirrors a service API, `typescript-professional-usage` or another language capability when exported types or idioms matter, `package-dependency-management` when publication changes dependency risk, and `change-documentation-gate` when examples or migration docs are part of the release.

Use **with** `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`, and `validation-broker` when the work must prove consumer graph reach, prior compatibility decisions, executed validators, and validation freshness.

# Proactive Professional Triggers

- **Signal:** Exported symbols, public types, config keys, generated operations, error classes, callbacks, extension points, defaults, or peer dependencies change.
  **Hidden risk:** a local compile pass hides a breaking SDK/library contract change for downstream consumers.
  **Required professional action:** classify the change class, run public-surface diffing, map consumers, and add compatibility or snapshot tests.
  **Route to:** `sdk-library-contract-design`, `api-contract-design`, `version-compatibility`.
  **Evidence required:** API-diff command/report, change-class rationale, consumer inventory, compatibility test output, and residual compatibility risk.
- **Signal:** OpenAPI/AsyncAPI/Protobuf/source spec, generator version, template, generated tree, package metadata, lockfile, or runtime floor changes.
  **Hidden risk:** nondeterministic generation or a silent runtime/dependency floor bump breaks installs and generated clients.
  **Required professional action:** pin source hash/generator digest/config, review generated diff, verify runtime matrix, and classify dependency risk.
  **Route to:** `sdk-library-contract-design`, `package-dependency-management`, `quality-test-gate`.
  **Evidence required:** source spec hash, generator pin, reproducible generation command, generated diff review, runtime matrix result, freshness timestamp, and package/dependency compatibility note.
- **Signal:** README, docs, examples, migration guide, changelog, deprecation marker, warning, or removal version changes near an SDK/library release.
  **Hidden risk:** docs and examples promise a contract that the packed artifact does not provide, or consumers miss a migration window.
  **Required professional action:** verify examples against the packed/installed artifact and require aligned changelog, migration, deprecation, removal policy, and docs generation command.
  **Route to:** `sdk-library-contract-design`, `change-documentation-gate`, `quality-test-gate`.
  **Evidence required:** packed-artifact example run, changelog entry, migration/deprecation map, docs/versioned reference output, and validator report.
- **Signal:** Package publishing, registry metadata, signature, provenance, SBOM, yanking, rollback, license, or security contact changes.
  **Hidden risk:** artifact provenance or rollback is unverifiable after publication, especially for immutable registries.
  **Required professional action:** record release artifact evidence, registry policy, provenance/SBOM/signature checks, and yank/hotfix plan.
  **Route to:** `sdk-library-contract-design`, `delivery-release-gate`, `package-dependency-management`.
  **Evidence required:** artifact digest/version, signature/provenance/SBOM verification with exit code and freshness, registry rollback/yank path, and release owner.
- **Signal:** Project memory, prior migration policy, consumer fixture, previous validation, or downstream smoke matrix is reused for a new SDK/library change.
  **Hidden risk:** stale consumer assumptions or old validation results are treated as current compatibility proof.
  **Required professional action:** inspect reused evidence against current source, current generated output, package graph, and consumer fixtures before accepting compatibility proof.
  **Route to:** `sdk-library-contract-design`, `project-memory-governance`, `execution-trajectory-analysis`.
  **Evidence required:** accepted/rejected memory table, validation freshness timestamp, changed-consumer delta, unknown consumer surfaces, and re-run or not-verified disclosure.

# Reference Loading Policy

- **L1:** Read this `SKILL.md` only for routing, small reviews, or compact SDK/library plans.
- **L2:** Read [references/checklist.md](references/checklist.md) when drafting/reviewing a concrete SDK/library contract plan, release checklist, consumer-compatibility review, or generated-client review.
- **L3:** Read [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when benchmark selection, graph-memory-execution coupling, or release-pattern evidence is material.
- **L3 output shape:** Read [examples/example-output.md](examples/example-output.md) when the user needs a filled SDK contract plan.
- **Do not load adjacent skills by default.** Load `api-contract-design`, `version-compatibility`, `package-dependency-management`, `quality-test-gate`, or language professional usage only when server API semantics, rollout sequencing, dependency graph risk, validation strategy, or language-specific exported API idioms are the primary concern.

# Risk Escalation Rules

- Escalate to `security-privacy-gate` when the SDK handles auth tokens, signing, payments, identity, or telemetry that may contain PII.
- Escalate to `delivery-release-gate` when the release touches public registries, signing keys, or yank policy.
- Escalate to critical when a breaking change is proposed for a public, partner-facing, mobile-embedded (long upgrade tail), or critical-infrastructure SDK without a co-shipped non-breaking adoption path.
- Escalate to `change-documentation-gate` when the change requires a migration guide, not just a CHANGELOG entry.
- Escalate to `package-dependency-management` when transitive dependency floors or peer-dependency ranges change.
- Escalate to legal when license, attribution, or export-control metadata changes.

# Critical Details

- Adding a new required parameter, narrowing a return type, removing an overload, removing a public field, renaming an exported symbol, changing an enum value, or making a class `final` / `sealed` is a major-version change.
- Adding a new optional parameter with a default, adding a new function, adding a new optional field to an output struct, or widening an input union is typically minor — but in some ecosystems (e.g., Rust trait method addition without default) it is breaking.
- Generator-floated output is a leading cause of accidental breaking releases; pin the generator container digest, lock file, and template version; review every regenerated diff.
- Pre-release tags (`-alpha`, `-beta`, `-rc`) on npm / PyPI are not installed by default ranges, but on crates.io they require explicit opt-in; document expectation per ecosystem.
- ESM vs CJS, `exports` map, `types` map, and `sideEffects` declaration are part of the npm contract surface; flipping module format is breaking.
- Python: `__all__`, `py.typed` marker, and exposed names in `__init__.py` define the contract; consider PEP 562 `__getattr__` for soft deprecation.
- Rust: `pub` items, MSRV (rust-version), trait coherence (sealed traits via private super-trait), and `#[non_exhaustive]` on enums / structs control compatibility surface.
- Java: binary vs source compatibility differ; adding a default interface method is source-compatible but may be binary-incompatible for some consumers; use `module-info.java` to constrain exports.
- Go: types added to a package, exported identifiers in `internal/` are not contract; v2+ paths (`example.com/foo/v2`) are required for breaking changes.
- Examples must be run against the published artifact in CI (`npm pack && npm install ./pkg.tgz`, `python -m build && pip install dist/*.whl`); examples that compile against source are not evidence.
- Telemetry hooks, plugin interfaces, and middleware contracts are extension surfaces and must be versioned independently if churn is expected.
- Yank / rollback policy must be documented: npm `deprecate`, PyPI `yank` (PEP 592), crates.io `yank`, Maven Central is immutable (must publish a fixed version).

# Failure Modes

- **Minor-breaking surface drift:** Symptom: strict-mode TypeScript consumers fail to compile after a minor release.
  Cause: an exported interface field was renamed; classified as minor.
  Detection: `api-extractor` diff in CI flags the rename; release blocked.
  Impact: forced rollback or emergency major release.
- **Floating generator drift:** Symptom: nightly downstream build flips between two generated client shapes.
  Cause: OpenAPI generator pulled `latest` tag.
  Detection: pin generator by digest; assert checksum of generated tree.
  Impact: nondeterministic SDK output, lost trust.
- **Example artifact mismatch:** Symptom: README example throws on `require('pkg')` after release.
  Cause: package added ESM-only `exports` map; README still shows CJS.
  Detection: example test installs packed artifact and runs both module systems if both are advertised.
  Impact: every onboarding fails.
- **Runtime-floor break:** Symptom: install fails for Node 18 consumers.
  Cause: minor release raised `engines.node` to ≥ 20.
  Detection: matrix CI on declared runtime floors; CHANGELOG check.
  Impact: broken installs across the consumer base.
- **Error taxonomy drift:** Symptom: downstream service errors out on new exception subclass.
  Cause: error taxonomy added a new subclass that downstream `instanceof` checks did not recognize.
  Detection: contract test enumerates throwable types and asserts hierarchy stability.
  Impact: production exception leak.
- **Deprecation without signal:** Symptom: deprecated API used in production with no warning.
  Cause: deprecation marker (`@deprecated`, `DeprecationWarning`, `#[deprecated]`) missing; only README mentioned it.
  Detection: lint rule requires runtime / build-time deprecation marker on any item flagged for removal.
  Impact: consumer surprise at major bump.
- **Unsigned artifact gap:** Symptom: artifact unsigned, no provenance.
  Cause: release pipeline skipped sigstore step when key rotation failed.
  Detection: post-publish gate verifies signature and SLSA attestation; release marked failed.
  Impact: supply-chain compliance gap, partner audit failure.
- **No rollback path:** Symptom: cannot rollback a published bug.
  Cause: no yank policy; or the registry is immutable (Maven Central).
  Detection: pre-release checklist requires yank / hotfix path per registry; for Maven, requires immediate fixed-version path.
  Impact: prolonged customer breakage.

# Output Contract

Return an `sdk_library_contract_plan` with:

- `contract_surface`: exported symbols, public types, error hierarchy, config keys, commands, generated operations, extension points, default values, peer dependencies
- `change_class`: patch / minor / major / internal-only with written justification and API-diff tool output reference
- `compatibility_matrix`: supported runtimes, OSes, package managers, module formats, server/API versions, prior SDK versions
- `generation_source`: source spec URL + hash, generator name + version + container digest, config file, reproducibility command, reviewed diff link
- `publication_plan`: registry, artifact names, signing (sigstore / GPG), provenance (SLSA), SBOM, CHANGELOG entry, release notes, yank/rollback procedure
- `examples`: runnable examples for primary flow, auth/config, pagination/streaming where relevant, one error path; CI invocation against packed artifact
- `consumer_tests`: API-diff, snapshot tests, Pact (or equivalent) contracts, fixture-consumer build, downstream smoke matrix list
- `deprecation_migration`: deprecated symbols, replacements, first-deprecated version, planned-removal version, migration steps, runtime warning mechanism
- `documentation_updates`: reference docs (generated), README, API docs versioned, migration guide, examples
- `graph_memory_execution_validation`: exports/package/generated/docs/consumer graph inspected, prior compatibility decisions reused or updated, commands run, evidence gaps
- `contract_to_validation_map`: each public-surface/generated/package/docs/release change mapped to diff, fixture, contract, example, package, provenance, or smoke validation
- `evidence_limits`: what local checks do not prove about downstream adoption, registry behavior, unpublished consumers, or future runtime/package-manager behavior
- `handoff`: owners for API, language runtime, docs, release engineering, security review

# Evidence Contract

An acceptable answer names:

- Repository evidence: export files, package metadata, generated output, source specs, examples, docs, changelog, deprecation markers, tests, fixtures, and release scripts inspected.
- Memory evidence: previous semver decisions, migration/deprecation windows, supported runtime floors, consumer commitments, and known compatibility exceptions accepted or changed.
- Graph evidence: package dependency graph, generated-client source graph, top consumers, fixture projects, downstream smoke matrix, and public/private export boundaries.
- Execution evidence: API-diff, generated diff review, packed-artifact install/example run, consumer fixture build, contract/smoke tests, SBOM/signature/provenance checks, and freshness after final edit.
- Boundaries inspected and limits: state package/export/generated/docs/consumer/release boundaries inspected, what evidence proves, what it does not prove, validation freshness, residual risk, and next handoff gate.
- Handoff evidence: next owner for API semantics, language idioms, docs, release, dependency/security review, residual risk, and rollback/yank/hotfix path.

# Benchmark Coverage

- **Compatibility:** semver/change-class discipline, public-surface diff, runtime floor stability, error taxonomy, default values, and deprecation-before-removal.
- **Generation:** pinned source spec, generator version/digest/config, reviewed generated diff, deterministic output, and source-vs-generated authority.
- **Consumer proof:** fixture-consumer builds, contract tests, downstream smoke matrix, packed-artifact examples, and old/new version compatibility checks.
- **Release integrity:** package metadata, changelog, migration guide, signatures/provenance, SBOM, registry policy, and rollback/yank behavior.

# Routing Coverage

This capability should route from prompts involving SDKs, generated clients, public libraries, published packages, reusable internal packages, exported APIs, public types, semver, package metadata, runtime floors, deprecations, examples, fixture consumers, downstream smoke tests, changelogs, and migration guarantees. Route away when the primary question is server API behavior, general dependency selection, language idiom review, release mechanics without SDK surface change, or application-only code with no reusable contract.

# Quality Gate

1. API-diff tool runs in CI and the diff has been reviewed and matches the declared `change_class`.
2. Generated clients (if any) are produced from a pinned spec hash + pinned generator digest; the diff has been reviewed.
3. CHANGELOG entry exists for every release and follows Keep a Changelog; every breaking and deprecated item appears.
4. Examples are executed against the packed/installed artifact in CI on every supported runtime floor.
5. Every supported runtime / package-manager combination is exercised by a matrix job; runtime floor is not silently raised.
6. Public exception / error hierarchy stability is asserted by a snapshot test.
7. Every deprecated item has a runtime / build-time deprecation marker, a documented replacement, and a removal version.
8. Release artifacts are signed and have SLSA build provenance + SBOM attached; verification step runs after publish.
9. Yank / rollback procedure is documented per registry and rehearsed at least once.
10. Downstream consumer smoke matrix (or Pact contract suite) passes against the release candidate before publish.
11. Repository graph evidence covers exports, generated files, package metadata, docs/examples, release scripts, and consumer fixtures in scope.
12. Every public-surface, generated-output, package, docs/example, and release-artifact change maps to a concrete validator or residual-risk owner.
13. Reused project memory, prior validation, and consumer fixtures are current or explicitly marked stale/not verified with follow-up owner.

# Used By

- data-api-contract-changer
- integration-change-builder
- change-documentation-gate
- quality-test-gate
- typescript-professional-usage
- package-dependency-management

# Handoff

Hand off to `api-contract-design` for service contract details, `version-compatibility` for rollout sequencing, `package-dependency-management` for dependency and publication risk, `change-documentation-gate` for docs and examples, `quality-test-gate` for consumer tests, and the matching language professional usage capability for idiomatic exported APIs.

# Completion Criteria

The capability is complete when the SDK or library surface is versioned, documented, tested against consumers, reproducibly generated or built, safely publishable, signed with provenance, and accompanied by explicit compatibility, deprecation, migration, and rollback guarantees.
