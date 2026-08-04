# SDK Library Contract Evidence Patterns

Use this reference when SDK/library closure depends on validation freshness, generated-client reproducibility, consumer compatibility evidence, publication provenance, stale prior evidence, or proof limits. Keep it as an evidence map, not a second SDK release guide.

## SDK Change-To-Validation Map

| SDK claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Public surface is compatible | Export paths, public API diff, type/signature snapshot, change-class rationale, and reviewed diff status | The inspected exported surface matches the declared semver class | Unpublished consumers, dynamic reflection, or undocumented extension use are compatible |
| Generated client is reproducible | Source spec hash, generator name/version/digest, config file, regeneration command, generated diff review | The generated output matches the declared source and toolchain | Future generator releases or uncommitted local templates remain stable |
| Runtime and dependency floors hold | Package metadata diff, lockfile or dependency range review, runtime/package-manager matrix command | The inspected release installs on declared runtime floors | Every consumer OS, package mirror, or optional dependency path is covered |
| Examples match artifact | Packed/installed artifact path, example command, exit code, and docs version | The published package entry points support the documented flow | Source-only examples, old docs, or downstream custom setup remain compatible |
| Consumer compatibility is current | Fixture project list, old/new build output, contract/smoke test report, and final-edit freshness | Known fixture consumers still build or pass against the release candidate | Unknown external consumers or private integrations are safe |
| Publication integrity is verifiable | Artifact digest, SBOM, signature/provenance check, registry metadata, and yank/hotfix owner | The release artifact can be traced and recovered according to the named registry policy | Registry outage, future credential compromise, or consumer upgrade timing is solved |

## Evidence Quality Labels

- **Strong evidence**: current export/package/generated/docs/consumer paths inspected, command or artifact named, exit code or review result recorded, final-edit freshness stated, and proof limits named.
- **Weak evidence**: local compile only, maintainer memory, changelog-only review, unpinned generator output, source-tree example run, or stale downstream smoke report.
- **Missing evidence**: no public API diff, no spec hash, no generated diff review, no fixture consumer, no packed-artifact example, no provenance/SBOM check, or no rollback/yank owner.
- **Invalid evidence**: semver class contradicts API diff, generated output from floating `latest`, docs example imports source internals, old validation predates final generated diff, or release artifact is unsigned when policy requires signing.

- If registry publish, yanking, deprecation, signing-key use, package token use, or external downstream smoke, require owner, dry-run or staging where available, rollback/yank/hotfix path, stop condition, and secret redaction.
