---
name: secret-configuration-security
description: "`analysis-agent`/`task-agent`/`review-agent`: use when secrets, KMS/env config, rotation, logging, redaction, or rollback changes; skip non-sensitive config."
---

# secret-configuration-security

## Registry Trigger

**Use when**

- secret or sensitive-config change affects exposure path, storage, access, redaction, rotation, revocation, or recovery
- rendered client, CI, image, log, manifest, or support artifact may expose credential material

**Do not use when**

- configuration change contains no secret or security-sensitive value and does not alter an exposure boundary

## Skill Role

Define secret creation, storage, distribution, use, rotation, revocation, redaction, and exposure response. Exclude general configuration and authentication semantics.

## High-Value Rules

- Trace changed values through source and history, CI variables and logs, build cache and image layers, client bundles and source maps, runtime manifests, observability sinks, support exports, backups, and offline consumers.
- Treat a plausibly exposed credential as compromised according to its authority and policy: contain access, rotate or revoke, verify consumer adoption, then decide whether history or artifact cleanup is also required.
- Design rotation as a state transition across known consumers. Define overlap or dual-read behavior when required, adoption evidence, revoke criteria, failure recovery, and a forward-safe rollback that does not revive compromised material.
- Scope storage and decrypt authority by principal, purpose, operation, environment, tenant, and lifetime; include audit, break-glass, deletion recovery, and inaccessible-consumer ownership where material.
- Keep raw values out of prompts, commands, diffs, fixtures, screenshots, reports, and retained scanner output. Validate transformation-aware redaction with representative secret-bearing shapes and downstream sinks.
- Separate sensitivity from mechanism: environment variables, encryption, masking, or a managed store do not by themselves prove least privilege, non-exposure, rotation safety, or recovery.
- Escalate security-sensitive defaults or config changes that weaken authentication, transport, authorization, isolation, rate control, or data protection; general config semantics remain with `configuration-runtime-policy`.

## Anti-Patterns

- Deleting a committed value, masking a CI setting, or removing one log line does not revoke copies already present in history, caches, artifacts, or external sinks.
- Public build prefixes, client-side config, serialized request objects, crash reports, and support exports can cross the intended audience boundary without an obvious “secret” field name.
- Rollback to an old compromised value is re-exposure, not recovery.

## Stop Conditions

- Escalate credible leaks, unknown consumers, broad decrypt/break-glass authority, unsafe rotation, unredacted sinks, unrecoverable key actions, evidence disclosure, or uninspected production-only paths.

## Output Contract

- Return a secret-configuration decision: map exposure, access scope, rotation, revocation, redaction, recovery, owner, and residual exposure

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | multiple exposure paths or rotation mechanisms remain plausible | one approved lifecycle resolves the changed secret boundary | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | secret or sensitive-config change affects exposure storage access rotation redaction or recovery | no secret or security-sensitive config boundary changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | no-leak least-privilege redaction rotation or recovery claims need fresh proof | no secret/config security claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
