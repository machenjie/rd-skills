# Requirement Clarification Evidence Patterns

Use this reference when clarification closure depends on current-source proof, repository inspection, prior task evidence, observable action sequence, validation freshness, forbidden-artifact scans, tool permission boundaries, or evidence limits. Keep it as an evidence map, not a second clarification tutorial.

## Clarification-To-Evidence Map

| Clarification claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Current behavior is known | Source path, doc/test/generated artifact, report, command output, or owner record inspected after the latest relevant edit. | The inspected boundary currently behaves or is specified as claimed. | Production-only data, unknown consumers, or uninspected routes match the claim. |
| Stakeholder claim is usable | Source, owner, scope, date/trigger, verification needed, and downstream Skill or owner recorded. | The claim can be carried as an explicit stakeholder assumption. | The claim is verified fact or safe for authority-owned behavior. |
| Blocking decision is valid | Question category, owner, decision shape, affected surface, and why answer can change contract/data/permission/release behavior. | Implementation would otherwise make an authority decision. | The owner will answer or the answer will be compatible. |
| Non-blocking decision is safe | Safe default, isolation method, not-present check, follow-up owner, expiry or trigger, and residual risk. | Work can proceed inside the named safe slice. | Adjacent work, public behavior, or later implementation will stay inside the slice without review. |
| Prior source or task evidence claim is accepted | Current source, registry/config/docs, tests, generated artifacts, or report confirms the repository inspection/prior evidence lead. | The lead is current enough for this clarification boundary. | A prior note alone proves product intent or all runtime callers. |
| Partial proceed is bounded | Can-implement-now list, must-wait list, forbidden assumptions/artifacts, owner response path, and review gate. | The approved safe slice is separated from blocked work. | The final implementation cannot drift into blocked work without a not-present scan. |
| Validation map is fresh | Each question, assumption, evidence claim, safe default, and forbidden artifact maps to a command, review check, owner answer, or residual risk. | Closure evidence matches the final clarification record. | Later edits, unrun validators, or unavailable telemetry are covered. |

## Current Evidence And Freshness

- Treat repository inspection, prior task evidence, old ticket comments, previous validations, generated artifacts, and observable action sequence as leads until current source confirms them.
- Accept a prior claim only while current evidence still matches. Examples include "requirement already decided", "route exists", "consumer does not depend on it", "permission is admin-only", and "data shape is clean". Evidence may include current source, owner records, reports, tests, generated artifacts, or telemetry.
- Reject or downgrade memory when it is undated, lacks owner, conflicts with current source, predates schema/generated/report changes, or names no validation path.
- Record observable action sequence when an agent already attempted diagnosis, asked questions, skipped a gate, or validated before the final clarification edit.
- Mark validation stale after edits to requirements, source files, tests, generated artifacts, reports, registries, docs, build/install outputs, or owner decisions.

## Forbidden-Artifact Checks

Use a not-present scan when partial proceed is allowed:

| Forbidden artifact | Example check |
| --- | --- |
| Public contract change | API/schema/generated client diff, export surface search, route table search. |
| Data or migration behavior | Migration directory search, model/schema diff, data-retention owner note. |
| Permission or tenant behavior | Auth policy search, denied-case acceptance, security gate handoff. |
| Release or rollout behavior | Flag/config/deploy script search, release gate handoff. |
| Hidden implementation of blocked work | Changed-path review, task diff, tests/docs scan for blocked term. |

- If owner record, ticket, telemetry, connector, or production-data lookup, record account/data boundary, redaction rule, retention, and unavailable evidence.
- If cleanup, migration, deploy, or external write, require owner approval, dry-run when available, rollback or compensation path, and stop condition.
