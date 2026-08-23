# Secret Configuration Security Evidence Patterns

- Keep raw values out of prompts, commands, diffs, fixtures, screenshots, reports, and retained scanner output. Validate transformation-aware redaction with representative secret-bearing shapes and downstream sinks.

Use this evidence-pattern Reference only when a no-leak, least-privilege, redaction, rotation, or recovery claim needs fresh proof; skip when no secret/config security claim awaits validation.

## Evidence Map

- **Source:** bind current detector/version, searched source/history/generated scope, reviewed sensitive paths, and limits; a miss does not prove history, providers, logs, or unscanned artifacts clean.
- **Frontend:** bind public-prefix rules, bundles/static configuration, source-map/CDN scope, environment labels, deployments and cache limits.
- **Logs and support:** bind safe allowlisted fields, representative secret-bearing shapes, observed sinks/audience/retention, and downstream/export limits.
- **Images and builds:** bind Docker/build configuration, image history/provenance, SBOM/report, cache boundary, base/tag limits, and raw-value exclusion.
- **Rotation:** bind known consumers, rollout order, redacted adoption/audit/health evidence, revoke criteria, rollback trigger, unknown/offline/cache/backup limits.
- **KMS or secret manager:** bind redacted policy diff, principal/purpose/operation/lifetime scope, deletion/recovery, audit and break-glass owner, runtime/emergency/drift limits.

## Evidence Quality And Authority

Strong evidence is current, final-edit fresh, scoped, redacted, reproducible, owner-attributed, and explicit about limits. Old scans, screenshots without policy diffs, masked settings without representative output, or unknown scope are weak. Missing scope/path/redaction/consumer/recovery/permission evidence remains a gap. Raw secrets, unsafe rollback, unredacted output, or approval substituted for no-leak proof is invalid.

Any provider/API read, CI/support export, rotation/revocation, KMS deletion, release, cleanup, sink or retention change requires an authorized owner, least privilege, bounded scope, redaction, stop, retention, and rollback/forward-fix boundary. Classify the claim before selecting proof.

