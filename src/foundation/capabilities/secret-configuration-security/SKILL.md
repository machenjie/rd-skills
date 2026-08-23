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

Own secret exposure, lifecycle, redaction, and recovery.

## High-Value Rules

- Map consumers and exposure paths before controls.
- Treat plausible exposure or unknown consumers as rotation gaps; masking or deletion is not revocation.
- Load named lifecycle/redaction/access/recovery References; exclude raw evidence.

## Anti-Patterns

- Local success substituted for evidence of the secret configuration security contract.

## Stop Conditions

- Stop on leaks, unknown consumers, broad decryption, unsafe rotation, unredacted sinks, unrecoverable keys, or uninspected production paths.

## Output Contract

- Return a secret-configuration decision: map exposure, access scope, rotation, revocation, redaction, recovery, owner, and residual exposure

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | multiple exposure paths or rotation mechanisms remain plausible | one approved lifecycle resolves the changed secret boundary | analysis-agent, task-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | secret or sensitive-config change affects exposure storage access rotation redaction or recovery | no secret or security-sensitive config boundary changes | analysis-agent, task-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | no-leak least-privilege redaction rotation or recovery claims need fresh proof | no secret/config security claim awaits validation | analysis-agent, task-agent, review-agent | evidence-record, proof-limit, residual-risk |
