# Secret Configuration Security Evidence Patterns

Use this reference when secret/config closure depends on scanner freshness, exposure-path proof, redaction validation, image/log/bundle inspection, rotation audit signals, stale prior evidence, tool-output retention, or proof limits. Keep raw secret values out of every artifact.

## Secret Config-To-Validation Map

| Secret/config claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current source is secret-free | Current scanner/report, searched path scope, reviewed `.env*`/docs/generated paths, and detector version or rule set | The inspected tree did not match the selected detectors and manual path review | Git history, old build logs, provider validity, or unscanned artifacts are clean |
| Frontend boundary is safe | Public-prefix rule, bundle/static config inspection, source-map/CDN scope, and reviewed env labels | Selected server-side secret labels are absent from inspected frontend artifacts | Older deployments, CDN caches, source maps outside scope, or unlisted env keys are safe |
| Logs/traces/errors are redacted | Allowlisted fields, representative payload, sink visibility, test/review artifact, and retention owner | Tested fields and sinks scrub selected secret-bearing values | Future field names, third-party processors, or every support export is covered |
| Container/build artifact is secret-free | Dockerfile/build config review, image history/provenance, SBOM or build report, and cache boundary | Inspected image metadata and build artifacts lack selected secret labels | Private build cache, base-image history, or other image tags are covered |
| Rotation sequence is safe | Consumer graph, rollout order, audit signal, health check, revoke criteria, and rollback trigger | Known consumers can adopt the new version before old revocation | Unknown consumers, long-lived caches, offline jobs, or backup copies are handled |
| KMS/secret-manager policy is least-privilege | Policy diff with raw values removed, principal scope, deletion/recovery window, audit source, and owner review | The inspected access policy matches named principals and lifecycle controls | Every runtime use, emergency path, or future policy drift is prevented |

## Evidence Quality Labels

- **Strong evidence**: current files/artifacts/log sinks inspected, command or manual review artifact named, exit code or owner result recorded, values redacted, final-edit freshness stated, and proof limits named.
- **Weak evidence**: old scan report, provider console screenshot without policy diff, masked CI setting without representative log output, prior claim, or scanner result with unknown scope.
- **Missing evidence**: no scan scope, no exposure path review, no redaction test, no rotation consumer list, no KMS recovery review, no tool permission boundary, or no owner for inaccessible logs/artifacts.
- **Invalid evidence**: raw secrets in output, real credentials in examples, rollback that revives a compromised secret, unredacted scanner output, or owner approval offered as proof that no leak exists.

- If provider console/API read, support export, CI log export, rotation, revocation, KMS deletion, release, or cleanup, require owner, least-privilege scope, stop condition, rollback/forward-fix path, output redaction, and retention boundary.
- Classify the secret/config risk as source, frontend, logs, image, rotation, or KMS policy before selecting proof.
