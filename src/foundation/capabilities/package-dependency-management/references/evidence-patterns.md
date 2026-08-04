# Package Dependency Evidence Patterns

Use this reference when dependency approval depends on repository inspection, prior task evidence, observable action sequence, validation freshness, tool permission boundaries, generated artifacts, or production evidence limits. Keep it as an evidence map, not a package-manager tutorial.

## Dependency Change-To-Evidence Map

| Dependency claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| New package beats simpler options | Need statement, stdlib/native/existing repository/existing dependency/local-code ladder, and at least two candidate packages | The inspected dependency add has a concrete reason and rejected alternatives | Future maintenance cost, advisory risk, or every product path is acceptable |
| Lockfile is reproducible | Manifest diff, lockfile diff, package-manager version, frozen install command, and exit code | The inspected environment resolves the named graph consistently | Other tool versions, registries, or platforms resolve identically |
| Transitive graph is bounded | `npm ls`, `pnpm why`, `pipdeptree`, `cargo tree`, `go mod graph`, `mvn dependency:tree`, or equivalent output plus package count | The inspected graph change and direct/transitive split are known | Hidden runtime imports, optional platform packages, or future registry changes are covered |
| License evidence is ready for handoff | Direct and new transitive licenses, outbound project license, scanner/report path, and accountable policy or legal owner | The inspected graph and distribution facts are recorded for the owner decision | Legal advice, downstream redistribution, or unscanned vendored artifacts are complete |
| Vulnerability evidence is ready for handoff | Advisory IDs, full selected-group scanner command/output, patched version or compensating control, owner, and expiration | The inspected advisory state is recorded for `dependency-vulnerability-scanning` | Risk is accepted, future CVEs, private advisories, or unselected exploit paths are absent |
| Lifecycle and provenance evidence is ready for handoff | Lifecycle script inventory, package source, maintainer/release health, OpenSSF/SLSA/SBOM evidence, and selected graph scope | The inspected supply-chain execution boundary is recorded for the accountable risk owner | Provenance risk is accepted, the package is immune to future compromise, or all registry mirrors are trustworthy |
| Runtime/deploy compatibility is covered | Target runtime, OS/libc/CPU/container image digest, native extension build output, and behavior test | The inspected dependency works on the selected deploy target | Every customer platform, downstream consumer, or production traffic shape is covered |
| Generated package output is fresh | Source schema/spec, generated output diff, drift check command, cache inputs, and committed/ignored policy | The inspected generated artifact matches its declared source of truth | External consumers or unpublished generated variants are compatible |
| Monorepo/package boundary stays valid | Workspace graph, hoisting/peer dependency check, isolated install/build, affected-test map, and forbidden import check | The inspected package can build within its declared boundaries | All publish/install modes or future workspace moves are safe |
| Rollback or repin path is viable | Previous pin/digest, downgrade command, migration reversal, release owner, and stop condition | The inspected dependency change has a named recovery path | Data migrations, third-party outages, or production rollback timing are guaranteed |

## Current Evidence And Freshness

- Treat prior task evidence, Renovate/Dependabot notes, old scan reports, generated dependency reports, and prior agent output as discovery inputs until current manifests, lockfiles, graph commands, scans, and tests confirm them.
- Accept a prior "safe dependency", "scan green", "license approved", "native build works", or "generated client current" claim only when current package-manager resolution, runtime target, generated artifacts, and validation commands still match.
- Mark evidence stale after edits to manifests, lockfiles, package-manager config, workspace layout, generated sources, container image digests, runtime versions, CI install mode, scanner config, fixtures, or build outputs.
- Record inspected and skipped boundaries: manifests, lockfiles, workspace config, package-manager version, generated outputs, container base images, native-extension platforms, CI install commands, vulnerability/license scanners, SBOM, package publishing, and prior exceptions.
- Map every final approval claim to a current command, report/artifact path, source diff, owner approval, or explicit not-verified residual risk.

- If package registry, advisory database, OpenSSF, SLSA/provenance, or license service lookup, cite source URL/service, timestamp, package coordinates, timeout, and absence of production credentials.
- If dependency publish, deploy, rollback, registry token use, production scanner, or connector write, require explicit owner, dry-run where available, stop condition, rollback/forward-fix path, and secret redaction rule.
