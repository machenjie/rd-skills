# Degraded Closure Contract

Load this reference when an adapter lacks complete stop, permission, validation, changed-path, lifecycle, compaction, or rollback visibility and closure depends on fallback/manual evidence.

## Contract Fields

- `supported_checks`: checks proven by current adapter events and visible fields.
- `unsupported_checks`: checks the adapter cannot observe, including event family, missing field, and closure consequence.
- `partial_checks`: checks where the event is visible but field coverage, ordering, freshness, or path scope is incomplete.
- `manual_fallback_evidence`: direct command logs, reports, source reads, diff inventory, screenshots, maintainer notes, or user confirmations used outside adapter support.
- `fail_policy`: fail-open warning, fail-closed block, owner, recovery path, and rollback note.
- `privacy_boundary`: retained bounded fields, excluded raw prompts/secrets/environment/full output, redaction marker, and retention class.
- `residual_risk`: what closure proves, what it does not prove, next owner, and next validation gate.

## Approval Rules

- Do not treat manual fallback evidence as adapter parity; mark the adapter capability as unsupported or partial.
- Fail-open warnings must appear in final handoff and closure residual risk.
- Fail-closed blocks need a configured rule, owner, operator recovery path, and rollback note before release.
- Unsupported validation freshness must route to `validation-broker` or explicit manual command evidence.
- Unsupported permission or sandbox visibility must route to `agent-tool-permission-sandbox` with a manual permission record.
