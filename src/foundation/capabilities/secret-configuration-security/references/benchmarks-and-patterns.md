# Secret Configuration Security Benchmarks And Patterns

Use this reference only when the root `SKILL.md` needs deeper support for benchmark-specific action, exposure-path validation, rotation sequencing, tool-output safety, or graph/memory/execution coupling. Keep raw secrets out of every note, example, report, and command transcript; use labels, fingerprints approved for disclosure, or placeholders.

## Benchmark Action Map

| Benchmark | Use When | Required Action | Evidence |
| --- | --- | --- | --- |
| OWASP Top 10 A02 / ASVS V2/V6 | Credential, key, token, session, API key, or encryption-control handling is in scope. | Prove storage, transport, entropy/lifecycle, access control, and redaction; rotate when exposed. | Source paths, config defaults, scanner output, redaction tests, owner review, and rotation record. |
| NIST SP 800-57 | Key generation, storage, use, rotation, revocation, destruction, or escrow is changed. | Define lifecycle phase, key owner, cryptoperiod, revocation trigger, destruction/recovery plan, and audit trail. | KMS policy excerpt with values removed, access audit, rotation schedule, backup/restore impact. |
| CIS Docker / SLSA | Container build, image, CI/CD, artifact provenance, or build-time secret use is in scope. | Keep runtime secrets out of layers; use runtime injection or BuildKit secrets; verify image history and provenance. | `docker history --no-trunc`, SBOM/provenance, CI log review, pinned artifact digest. |
| Provider secret manager | Vault, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault, or equivalent stores a secret. | Use versioning, least-privilege identity, audit logging, rotation, deletion window, and break-glass policy. | Secret path label, policy summary, audit-log source, access-review record, recovery window. |
| SOC 2 / GDPR Article 32 | Credentials guard systems that process regulated or customer data. | Preserve access-review, rotation, incident, and remediation evidence; minimize exposure in logs and support tools. | Approval record, access-review cadence, redacted incident evidence, retention owner. |

## Exposure Path Matrix

| Path | Primary Risk | Verification Pattern | Handoff |
| --- | --- | --- | --- |
| Git source and history | Literal or generated secret persists after deletion. | Current scanner plus history-aware scan when exposure is plausible; inspect `.env*`, examples, fixtures, docs, and generated files. | Rotate/revoke first, then history rewrite plan if needed. |
| CI/CD logs and variables | Masking gaps, debug echo, transformed values, broad log access. | Review workflow definitions, representative job output, masking rules, and log visibility. | Security gate plus delivery gate for pipeline changes. |
| Container image and build cache | Build args, copied files, or metadata expose secrets. | Verify Dockerfile/build config, image history, SBOM/provenance, and cache behavior. | Delivery gate for rebuild, rollout, and artifact replacement. |
| Frontend bundle | Public prefixes publish server-side secrets to users. | Inspect env prefix rules, bundle output, static config, HTML, source maps, and CDN artifacts. | Web/security owner plus rotation when exposed. |
| Logs, traces, metrics, errors | Secret values fan out to observability/support audiences. | Require allowlist redaction tests against representative payloads and downstream sink visibility. | Logging owner plus reliability/observability gate. |
| KMS and secret-manager policy | Overbroad decrypt, deletion without recovery, cross-account access. | Review policy diff, principal scope, deletion window, audit log, and restore/decrypt impact. | Security owner plus reliability/delivery gates before release. |

## Rotation And Revocation Pattern

1. Inventory every consumer by repository graph, deployment manifests, jobs, support tools, and owner confirmation.
2. Create the new secret version in the approved store without exposing the raw value in source, logs, docs, or chat.
3. Update consumers through a rollout that tolerates old and new values during the transition when protocol semantics require it.
4. Verify consumer adoption with audit logs, health checks, error-rate watch, and rollback trigger.
5. Revoke the old version only after adoption evidence is current; do not treat old-secret resurrection as rollback.
6. Record residual risk, inaccessible consumers, stale memory, and any unverified log/container/frontend paths.

## Graph, Memory, And Execution Coupling

- Repository graph decides which source, generated files, manifests, docs, CI, container, frontend, log, and support-tool paths must be inspected.
- Project memory can identify prior leaks, fragile files, previous scanner gaps, or owner decisions, but it is a selector, not proof.
- Execution trajectory decides whether validation ran after the final material edit, whether a risky command printed sensitive output, and whether repeated failure changed route.
- Validation broker maps each changed secret/config boundary to a scanner, test, build check, policy review, owner response, release gate, or explicit residual risk.
- Agent-tool permission/sandbox evidence is required before running broad scanners, release tools, connector reads, support exports, cleanup scripts, rotation, revocation, or KMS deletion actions.

## Validation Command Map

| Claim | Example Evidence Type | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| No source secret in current tree | Current scanner output and reviewed paths. | Detector rules did not match inspected paths. | Git history, external logs, unscanned generated artifacts, or real provider validity. |
| No frontend exposure | Bundle/static artifact inspection and prefix review. | Inspected bundle does not contain selected server-secret labels. | CDN caches, source maps, older releases, or unlisted environment keys. |
| Redaction works | Representative log/trace/error test. | Selected fields and sinks are scrubbed for the tested payloads. | Future field names, untested serializers, or third-party processor behavior. |
| Image has no build secret | Docker history/provenance review. | Inspected image metadata lacks known secret labels. | Other images, private build cache, base-image history, or registry access logs. |
| Rotation is safe | Consumer graph, audit signal, health check, rollback trigger. | Known consumers adopted the new version within the observed window. | Unknown consumers, long-lived caches, offline jobs, or old backups. |

## Anti-Pattern Review Questions

- Does any example value look realistic enough that a reader might copy it into production?
- Does any support, debug, migration, or admin path bypass normal redaction or authorization controls?
- Does a config-only change weaken TLS, auth, rate limit, CORS, CSP, WAF, DNS/CDN exposure, KMS, or deletion behavior?
- Does a scanner or validation command create a new raw-output artifact that needs retention and redaction policy?
- Does the rollback plan depend on reviving an old compromised secret instead of a forward-safe mitigation?
- Does the final handoff distinguish owner approval from technical proof and scanner absence from proof of no leak?
