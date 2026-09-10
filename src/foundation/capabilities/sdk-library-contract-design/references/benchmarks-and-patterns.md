# SDK Library Contract Design Benchmarks And Patterns

Load for a named versioning, generated-client, compatibility, adoption, or publication decision; skip when ecosystem policy and current consumer evidence already select the path.

## Compatibility Choice Matrix

| Surface | Evidence | Hidden risk |
| --- | --- | --- |
| Exports and public types | API diff, signature snapshot, compatibility rationale. | Rename, narrowing, abstract member, enum, reflection, or exhaustive-match break. |
| Generated operations/models | Spec hash, generator/template/config pin, reproducible diff. | Floating tools or local templates reshape clients. |
| Errors/defaults/behavior | Negative contract tests and old/new fixtures. | Retry, overload, serialization, or implicit-default drift. |
| Runtime/dependency floors | Package metadata and supported runtime/package-manager matrix. | A nominally minor release no longer installs. |
| Examples/docs | Packed-artifact examples and versioned docs build. | Source-only or stale examples pass. |
| Publication | Digest and source/build provenance, registry metadata, recovery owner, and applicable SBOM or signature evidence. | Artifact integrity or recovery is unproved. |

## Benchmark Evidence

- Apply the governing ecosystem policy before SemVer, Cargo SemVer, Haskell PVP, pre-1.0, or date-based service-version labels.
- Compare the before/after public surface using API Extractor reports, `cargo semver-checks`, Revapi, japicmp, Go `apidiff`, .NET `ApiCompat`, `griffe check`, or the appropriate ecosystem equivalent.
- Treat `pyright --outputjson` as type-check diagnostics for the checked source or consumer fixtures. It does not itself compare public surfaces across versions; unreferenced export removal can escape current-source diagnostics.
- For generated surfaces, bind source specification, generator and template version or digest, configuration, committed output, reviewed semantic diff, and regeneration command.
- Build representative consumers against the packed artifact across supported environments and affected calls, errors, configuration, and generated code.
- Record changelog/deprecation/migration evidence plus applicable signature, provenance, SBOM, OSV, SLSA, licensing, and registry recovery ownership.

## Adoption And Handoff

- Classify patch, minor, major, or internal-only from exported, binary, wire, behavioral, packaging, runtime, and ecosystem evidence.
- Select mixed-version adoption, removal timing, rollback, or yank only from current consumer and persisted/wire compatibility evidence.
- Route server semantics to `api-contract-design`.
- Route rollout windows to `version-compatibility`.
- Route dependency and provenance depth to package and security owners.
- Route documentation publication to its owner.
- Route test depth to quality and validation owners.
- Record unknown external consumers, private extensions, optional dependencies, mirrors, future generators, registry outages, and consumer timing as proof limits.
