# Containerization Evidence Patterns

Use this reference when containerization closure depends on validation freshness, prior source or task evidence claims, artifact-to-runtime proof, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second container hardening checklist.

## Artifact-To-Validation Map

| Container claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Image definition graph is complete | Dockerfile/Containerfile, build context, entrypoint, compose/orchestrator refs, CI image build, deploy image refs, and same-pattern search | Inspected image artifacts and deployment consumers are known | Hidden registries, manual deploys, or future generated manifests are covered |
| Runtime image is minimal | Build/runtime stage diff, explicit artifact copy list, package list or image inspection, and rejected base alternatives | Inspected runtime stage excludes obvious build-only tools | Future base updates or dynamic downloads keep the same surface |
| Image is secret-free | `.dockerignore`, secret scan, build-arg/env review, layer/history inspection or equivalent, and runtime secret-source owner | Inspected layers and build context avoid obvious credential leaks | All private registry, CI log, or cache exposures are ruled out |
| Non-root runtime is usable | User/group, ownership, writable path, read-only-rootfs decision, and runtime smoke or review artifact | Inspected process can run without root for declared paths | Platform security context or production volume behavior is fully proven |
| Health and shutdown behavior is accurate | Probe contract, exec-form entrypoint, SIGTERM/init review, exposed port check, and start/stop evidence | Inspected container has declared readiness and termination behavior | Production traffic drain or orchestrator timing is fully proven |
| Supply-chain evidence is fresh | Digest pin, SBOM path, vulnerability scan summary, signing/provenance record, and exception owner | Inspected artifact has current build-time supply-chain evidence | Future CVEs, registry admission, or cluster policy are covered |
| Rollback is content-addressed | Prior digest, promotion path, deploy reference, registry availability, and rollback owner | The inspected release can name a concrete rollback artifact | Rebuilt mutable tags or unavailable registries will work during incident |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old digests, runbooks, registry reports, and previous scans as selectors until current source and fresh validation confirm them.
- Accept prior "base is approved", "image runs non-root", "secrets are excluded", or "scan is clean" claims only when current Dockerfile, context, CI, deploy refs, and final image evidence still match.
- Mark evidence stale after edits to Dockerfile, Containerfile, `.dockerignore`, entrypoint, lockfiles, base digests, deploy manifests, CI image build, scan reports, SBOMs, or generated artifacts.
- Map each final image or deployment claim to current evidence: command, test, report, registry artifact, owner review, or explicit not-run residual risk. Coverage includes affected image claims, exceptions, deploy references, runtime behavior, scan results, and handoffs.

- If registry push, signing, deployment, rollback, or live probe change, record environment, owner approval, stop condition, rollback path, and redaction rule.
- If production registry, telemetry, or admission-policy query, keep access read-only or approved-connector-scoped and redact image labels, tenant data, secrets, and credentials.
