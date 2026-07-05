# Package Dependency Evidence Patterns

Use this reference when dependency approval depends on repository graph, project memory, execution trajectory, validation freshness, tool permission boundaries, generated artifacts, or production evidence limits. Keep it as an evidence map, not a package-manager tutorial.

# Dependency Change-To-Evidence Map

| Dependency claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| New package beats simpler options | Need statement, stdlib/native/existing repository/existing dependency/local-code ladder, and at least two candidate packages | The inspected dependency add has a concrete reason and rejected alternatives | Future maintenance cost, advisory risk, or every product path is acceptable |
| Lockfile is reproducible | Manifest diff, lockfile diff, package-manager version, frozen install command, and exit code | The inspected environment resolves the named graph consistently | Other tool versions, registries, or platforms resolve identically |
| Transitive graph is bounded | `npm ls`, `pnpm why`, `pipdeptree`, `cargo tree`, `go mod graph`, `mvn dependency:tree`, or equivalent output plus package count | The inspected graph change and direct/transitive split are known | Hidden runtime imports, optional platform packages, or future registry changes are covered |
| License posture is acceptable | Direct and new transitive licenses, outbound project license, scanner/report path, and owner verdict | The inspected graph has no known incompatible license | Legal advice, downstream redistribution, or unscanned vendored artifacts are complete |
| Vulnerability decision is current | Advisory IDs, scanner command/output, patched version or compensating control, owner, and expiration | The inspected advisory state was triaged against the current graph | Future CVEs, private advisories, or unselected exploit paths are absent |
| Install scripts and provenance are controlled | Lifecycle script inventory, package source, maintainer/release health, OpenSSF/SLSA/SBOM evidence, and allowlist decision | The inspected supply-chain execution boundary is known | The package is immune to future compromise or all registry mirrors are trustworthy |
| Runtime/deploy compatibility is covered | Target runtime, OS/libc/CPU/container image digest, native extension build output, and behavior test | The inspected dependency works on the selected deploy target | Every customer platform, downstream consumer, or production traffic shape is covered |
| Generated package output is fresh | Source schema/spec, generated output diff, drift check command, cache inputs, and committed/ignored policy | The inspected generated artifact matches its declared source of truth | External consumers or unpublished generated variants are compatible |
| Monorepo/package boundary stays valid | Workspace graph, hoisting/peer dependency check, isolated install/build, affected-test map, and forbidden import check | The inspected package can build within its declared boundaries | All publish/install modes or future workspace moves are safe |
| Rollback or repin path is viable | Previous pin/digest, downgrade command, migration reversal, release owner, and stop condition | The inspected dependency change has a named recovery path | Data migrations, third-party outages, or production rollback timing are guaranteed |

# Graph, Memory, And Execution Reconciliation

- Treat project memory, Renovate/Dependabot notes, old scan reports, generated dependency reports, and prior agent output as discovery inputs until current manifests, lockfiles, graph commands, scans, and tests confirm them.
- Accept a prior "safe dependency", "scan green", "license approved", "native build works", or "generated client current" claim only when current package-manager resolution, runtime target, generated artifacts, and validation commands still match.
- Mark evidence stale after edits to manifests, lockfiles, package-manager config, workspace layout, generated sources, container image digests, runtime versions, CI install mode, scanner config, fixtures, or build outputs.
- Record inspected and skipped boundaries: manifests, lockfiles, workspace config, package-manager version, generated outputs, container base images, native-extension platforms, CI install commands, vulnerability/license scanners, SBOM, package publishing, and prior exceptions.
- Map every final approval claim to a current command, report/artifact path, source diff, owner approval, or explicit not-verified residual risk.

# Tool Permission Boundary

| Action | Boundary record |
| --- | --- |
| Local source reads, registry search, lockfile diff, and report inspection | Read-only local shell action; cite paths, searched patterns, and avoid full output dumps |
| Local graph commands, frozen install, scanner, test, build, SBOM, and generated drift checks | State-mutating only for caches, reports, temp files, build/dist artifacts, or local dependency stores; cite command, exit code, log path, sandbox, network state, and cleanup |
| Package registry, advisory database, OpenSSF, SLSA/provenance, or license service lookup | Network-sensitive read; cite source URL/service, timestamp, package coordinates, timeout, and absence of production credentials |
| Dependency publish, deploy, rollback, registry token use, production scanner, or connector write | High-risk action; require explicit owner, dry-run where available, stop condition, rollback/forward-fix path, and secret redaction rule |

# Handoff Evidence Shape

```yaml
package_dependency_evidence_closure:
  inspected_boundaries:
    - boundary: ""
      current_source_or_artifact: ""
      finding: ""
  accepted_prior_claims:
    - claim: ""
      current_evidence: ""
      freshness: ""
  rejected_or_stale_claims:
    - claim: ""
      reason: ""
  dependency_to_validation_map:
    - dependency_decision: ""
      source_path_or_artifact: ""
      command_or_gate: ""
      exit_code_or_status: ""
      proves: ""
      does_not_prove: ""
      owner: ""
  tool_permission_boundary:
    action_class: ""
    sandbox: ""
    state_mutation: ""
    network_or_registry_access: ""
    redaction: ""
  residual_risk:
    - risk: ""
      owner: ""
      next_gate: ""
```
