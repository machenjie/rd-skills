# Documentation Evidence Patterns

Use this reference when documentation closure depends on source freshness, consumer impact, generated artifacts, rendered output, link/spec validation, retention, or safe disclosure. Keep it as proof guidance, not a second writing style guide.

## Claim-To-Evidence Map

| Documentation claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Docs match changed behavior | Source/config/schema path, docs path, before/after delta, reviewer, and command or manual check | Inspected docs reflect the final reviewed change | Readers have adopted the new behavior |
| API docs are current | Source route/schema, generated spec or docs path, changed fields/errors, compatibility note, and validation command | Published contract artifact is aligned for inspected endpoints | Every external consumer is compatible |
| Migration guide is actionable | Affected version, pre/post steps, rollback or validated alternative recovery with rollback limits, expected output, owner, and dry-run or review status | A trained operator or consumer has a documented path | Live rollback will succeed under every incident |
| Runbook is executable | Alert trigger, dashboard/query/log command, expected result, escalation path, and rehearsal or review | On-call has concrete triage and escalation steps | Production symptoms will always match the runbook |
| No-docs decision is safe | Affected audience scan, inspected docs, behavior-delta rationale, validation signal, and residual risk | No obvious audience-facing doc update was needed | Hidden consumers or unpublished docs are absent |
| Security disclosure is safe | Public/private boundary, redaction rule, sensitive detail scan, approval owner, and retained evidence path | Obvious secrets and sensitive internals were not knowingly published | Every future mirror, export, or support reply is safe |
| Compliance evidence is retained | Control objective, artifact path, owner, approval source, freshness date, exception owner, and retention period | Evidence can be traced for the inspected control | Auditor interpretation or future control design is approved |

For standalone documentation, check requested text or diagrams against supplied facts or their owning source. This supports content accuracy; it does not establish a runtime behavior change or demonstrate reader comprehension. Use the behavior-delta evidence above only when claiming that docs match changed behavior.

## Freshness Rules

- Mark documentation evidence stale after changes to public behavior, schemas, generated specs, CLI help, config defaults, feature flags, runbook alerts, rollout/rollback mechanics, docs examples, or release notes.
- Treat generated specs, diagrams, screenshots, rendered docs, and reports as selectors until the final source and validation command confirm them.
- If a source changes after documentation validation, repeat affected checks or explain why the documented claims remain valid. Standalone prose edits need no unrelated code review.
- When current source, prior docs, prior task evidence, and generated artifacts disagree, prefer current source plus fresh validation and record stale artifacts explicitly.

- If publishing docs, notifying customers, updating status page, sending compliance packet, require owner approval, audience, rollback/update path, and safe-disclosure review.
- If reading production logs, support cases, customer data, or audit systems, require data class, redaction, retention, and approval boundary.
- For tasks spanning multiple artifacts, classify inspected surfaces as source, docs, spec, runbook, release, or compliance and record relevant status, validation, and owner.
