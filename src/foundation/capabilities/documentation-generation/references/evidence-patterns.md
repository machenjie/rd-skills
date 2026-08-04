# Documentation Generation Evidence Patterns

Use this reference when documentation closure depends on claim-to-source mapping, generated or executable example freshness, no-docs proof, stale prior source or task evidence claims, command safety, tool permission boundaries, or proof limits. Keep it as an evidence map, not a second documentation guide.

## Documentation-To-Evidence Map

| Documentation claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Documented behavior matches source | Current source/schema/config/test path, changed behavior summary, doc path, and reviewer or validator artifact | The inspected doc claim reflects the inspected source | Uninspected variants, future source changes, or production state |
| Example or command is safe and current | Command/snippet source, run/regenerate result or not-run label, expected output, preconditions, and rollback when mutating | The reader can see the command's verified or limited status | Every environment, credential scope, or destructive path is safe |
| API/config docs match authority | Authoritative spec/schema/config path, defaults/errors/compatibility note, and contract validation or diff | The inspected contract docs align with the named authority | All generated clients or external consumers are compatible |
| Migration or release docs are actionable | Upgrade order, rollback or forward-fix, version-skew window, owner, and validation command/report | The documented rollout path is bounded for the inspected release | Actual production rollout success or every consumer adoption path |
| Runbook is operable | Trigger, impact, triage action, expected output, failure signal, escalation, signal owner, and validation method | On-call can distinguish success from failure for the inspected procedure | The alert threshold or live incident path is complete |
| No-docs decision is justified | Changed paths, audience map, searched docs/artifacts, no-change rationale, and stale-doc trigger | Durable docs were considered for the inspected change | Hidden audiences, external docs, or future release packaging |
| Generated docs are fresh | Generator input path, command, output artifact, source/spec diff or validator, and final-source freshness | The generated artifact was compared to current inputs | The generator itself is semantically correct in every case |
| Sensitive content is avoided | Secret/PII/private-topology check, safe placeholders, redaction rule, and residual exposure owner if partial | The inspected docs avoid known sensitive disclosures | Historical docs, screenshots, or third-party copies are clean |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, previous handoffs, generated docs, and old examples as discovery inputs until current source, docs, and validation confirm them.
- Accept prior "docs are current", "example works", "runbook exists", or "no docs needed" claims only when current source, audience, docs, and final validation still match.
- Mark evidence stale after edits to source behavior, schemas, configs, public exports, docs, generated inputs/outputs, examples, commands, validators, reports, or build outputs.
- Map every final documentation claim to a source path, command, generated artifact, validation report, owner review, or explicit not-verified residual risk.

- If command snippets that mutate files, data, infrastructure, credentials, or external systems, record preconditions, dry-run or sandbox, rollback/forward-fix, owner, and redaction rule.
- If connector, ticket, wiki, cloud console, or production telemetry supports documentation, treat it as external or credential-scoped, use bounded approved credentials when required, and record scope, timestamp, redaction, and owner.
