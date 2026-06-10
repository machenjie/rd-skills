---
name: change-documentation-gate
description: Ensures affected documentation is updated for product and code changes, including README, API docs, migration notes, ADRs, changelog, runbooks, troubleshooting, user docs, operational notes, and release communication.
license: MIT
changeforge_kind: professional-skill
changeforge_version: 0.1.0
---

# Change Documentation Gate

## Mission
Ensure every change leaves accurate, audience-appropriate documentation exactly where the affected audience needs it — and that undocumented behavior, broken migrations, missing runbooks, and silent breaking changes are blocked from release until their documentation debt is resolved or explicitly accepted with rationale.

## When To Use
- Before merge, release, or support enablement when any of the following change: user-facing behavior, public or internal API contracts, data migrations or schema changes, operational runbooks or alert thresholds, architecture decisions, configuration or environment variables, or security posture.
- When a new component, service, feature flag, or integration is added that operators, developers, or users must understand.
- When a breaking change is introduced that requires migration guidance for consumers.
- Before release when release notes, communication plans, or changelog entries are required.
- During or after customer-impacting incidents when an incident report, customer advisory, status page entry, postmortem summary, or corrective action tracker is required.
- When regulated or audited systems need control mapping, evidence packets, exception approvals, or evidence retention documentation.

## Do Not Use When
- The change is purely an internal refactor with zero behavioral change — no user, operator, integrator, or developer context shifts.
- The change is a cosmetic edit (whitespace, comment reformatting, test data cleanup) that affects no documented behavior or contract.
- The change is a revert of a recently merged commit where no documentation was yet published to consumers.

## Non-Negotiable Rules
- Update documentation that real users or operators depend on — never let "it's in the code" serve as user or operator documentation.
- Preserve accuracy over volume: a correct one-sentence update is superior to a verbose misleading paragraph.
- Never expose secrets, credentials, internal IP addresses, or security-sensitive implementation details in public-facing documentation.
- Breaking changes and deprecations must have migration guides before the change ships — not promised "later."
- Runbooks and troubleshooting guides must be updated before a new alert, SLO, or operational procedure goes live.
- ADRs (Architecture Decision Records) must be written before irreversible architecture decisions are implemented — retroactive ADRs lose their decision-support value.
- Changelogs must be human-readable summaries for the affected audience, not commit log dumps.
- Documentation ownership must be assigned — unowned documentation accumulates as unmaintainable drift.
- Incident and compliance documentation must preserve evidence integrity: every customer advisory, status page entry, postmortem action, control mapping, and exception approval needs owner, timestamp, and retention target.

## Industry Benchmarks
- **Docs-as-Code (Write the Docs standard)**: Documentation is versioned alongside code, reviewed in pull requests, and owned by engineers — not a separate post-release activity.
- **OpenAPI 3.0 / AsyncAPI 2.0**: Machine-readable API documentation standards — required for any HTTP or event-driven API used by more than one team.
- **Architectural Decision Records (ADRs - Michael Nygard format)**: `Status`, `Context`, `Decision`, `Consequences` — written before implementation for irreversible decisions.
- **DORA Metrics (Documentation as a deployment risk factor)**: Teams with poor documentation coverage have significantly longer incident recovery times.
- **RFC 7807 (Problem Details)**: Error responses in API documentation must include human-readable and machine-readable formats.
- **Google Developer Documentation Style Guide**: Clear, concise, audience-appropriate technical writing — active voice, second person, task-oriented structure.
- **ITIL / SRE Runbook Standard**: Operational procedures must include preconditions, step-by-step actions, expected outputs, failure indicators, and escalation path.

### Documentation Impact Matrix

| Change Type | Required Documentation | Audience |
|---|---|---|
| New user-facing feature | User guide, changelog, release notes | End users |
| API endpoint added/changed | OpenAPI spec, migration guide (if breaking), changelog | API consumers, developers |
| Breaking API change | Deprecation notice, migration guide, versioning strategy | API consumers |
| Schema / data migration | Migration script, rollback steps, data owner notification | Database admins, operators |
| New configuration / env var | README or config reference, default values, required vs. optional | Operators, developers |
| Architecture decision | ADR with context, decision, alternatives, consequences | Engineering team |
| New alert / SLO / runbook | Runbook with triage steps, escalation path, alert description | SRE, on-call engineers |
| Security posture change | Security impact statement, user-visible behavior change notice | Security team, users |
| Dependency upgrade (major) | Changelog summary, migration notes if API-breaking | Developers |
| Customer-impacting incident | Incident report, customer advisory, status page entry, postmortem summary, corrective action tracker | Customers, support, SRE, leadership |
| Regulated or audited change | Control mapping, approval evidence, audit packet, exception record, retention note | Auditors, compliance, security, release owners |

## Technical Selection Criteria
Evaluate documentation requirements across these dimensions:
- **Audience identification**: Who reads this documentation? Users, operators, API consumers, developers, auditors?
- **Behavioral delta**: What observable behavior changed that an informed reader could not infer without documentation?
- **Contract impact**: Did any API shape, error code, field name, configuration key, or CLI argument change?
- **Migration requirement**: Does a consumer need to take action before or after upgrading? Is the action documented?
- **Operational impact**: Does an on-call engineer need a new runbook entry, modified alert description, or updated triage procedure?
- **Security and privacy disclosure**: Does the change require a security advisory, privacy notice update, or compliance evidence update?
- **Deprecation lifecycle**: Is this change part of a deprecation — with a declared timeline, migration path, and notification to affected consumers?
- **ADR necessity**: Is this an irreversible or difficult-to-reverse architecture decision that needs documented reasoning?
- **Incident documentation**: Is there an incident report, customer advisory, status page entry, postmortem summary, and corrective action tracker with owners?
- **Compliance evidence chain**: Which control objective, evidence artifact, evidence owner, approval record, exception owner, and retention period must be documented?

## Mode Matrix
Select the documentation gate mode before deciding whether docs changed.

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
|---|---|---|---|---|---|
| No-docs decision | Internal refactor or cosmetic change claims no audience behavior changed. | Prove no user, operator, API, developer, auditor, or release behavior changed. | Affected audience scan and no-change rationale tied to files/contracts. | `change-impact-analyzer`, `code-review` | Changelog entry when no audience-facing behavior exists. |
| User/API documentation | User behavior, API shape, error code, CLI, config, or integration contract changes. | Put update where the affected audience already looks and preserve migration clarity. | Artifact path, audience, before/after behavior, migration/consumer note. | `data-api-contract-changer`, `acceptance-criteria-builder` | Runbook/ADR unless operational or architecture behavior changes. |
| Migration/release docs | Schema, data migration, deprecation, version skew, rollout, rollback, or release note. | Document operator action, rollback, compatibility, and consumer timing before release. | Migration note, rollback steps, changelog/release note, owner and deadline. | `delivery-release-gate`, `release-rollback` | User docs when only operator behavior changes. |
| Operational/runbook docs | Alert, SLO, dashboard, incident response, support flow, or troubleshooting path changes. | Keep on-call and support procedures executable under pressure. | Runbook path, trigger, expected output, escalation, validation command. | `reliability-observability-gate`, `failure-diagnosis` | API migration docs unless contract changed. |
| ADR/compliance evidence | Irreversible architecture, security posture, audit control, incident, or exception evidence. | Preserve decision/evidence integrity with owner, timestamp, retention, and residual risk. | ADR/control artifact, approval source, exception/retention owner, evidence freshness. | `architecture-impact-reviewer`, `security-privacy-gate` | Marketing or catalog copy. |

## Proactive Professional Triggers
These triggers are hidden-risk escalators, not ordinary checklist items.

- **Signal:** A code or config change changes behavior but no docs are touched and no no-docs rationale is stated. **Hidden risk:** users/operators/API consumers learn behavior by failure. **Required professional action:** require documentation matrix or evidence-backed no-change decision. **Route to:** `change-impact-analyzer`, `quality-test-gate`. **Evidence required:** affected audience list, artifact scan, no-change rationale or update path.
- **Signal:** API field, error code, CLI flag, env var, webhook, or event schema changes without docs. **Hidden risk:** consumer integration breaks or config is misapplied. **Required professional action:** update contract docs or block release. **Route to:** `data-api-contract-changer`, `contract-testing`. **Evidence required:** spec path, migration note, consumer notification status, validation command.
- **Signal:** API/SDK/schema/event/public export change has unknown consumers or no migration/deprecation note. **Hidden risk:** silent breaking change reaches generated clients, mobile apps, backend integrations, or package consumers. **Required professional action:** document consumer impact, compatibility path, telemetry, and rollout/rollback. **Route to:** `consumer-impact-analysis`, `data-api-contract-changer`. **Evidence required:** changed contract, consumer list, migration guide, deprecation policy, telemetry, and tests.
- **Signal:** feature flag, runtime mode/kind switch, kill switch, tenant/user/experiment config, or default changes without owner, expiry, or cleanup docs. **Hidden risk:** configuration becomes a permanent hidden policy system or bypasses invariants. **Required professional action:** document typed config, validation, fail-fast behavior, flag lifecycle, cleanup owner/date, and rollout safety. **Route to:** `configuration-runtime-policy`, `delivery-release-gate`. **Evidence required:** config schema, default behavior, validation behavior, flag owner, expiry, and cleanup path.
- **Signal:** feature flag, fallback, compatibility branch, deprecated API, or generated compatibility shim is retained or removed with no deletion plan. **Hidden risk:** stale behavior persists forever or deletion breaks runtime/reflection consumers. **Required professional action:** document cleanup/deletion governance. **Route to:** `cleanup-deletion-governance`, `refactoring`. **Evidence required:** target artifact, owner, removal condition, caller search, telemetry, rollback path, and tracking issue.
- **Signal:** architecture rules are documented but import/cycle/export/forbidden dependency checks are not wired into CI. **Hidden risk:** architecture drift is invisible until review or production defects. **Required professional action:** document enforcement tooling, CI command, generated-code exceptions, and migration path. **Route to:** `architecture-enforcement-tooling`, `architecture-impact-reviewer`. **Evidence required:** rule list, tool choice, CI command, failure examples, exceptions, and owner.
- **Signal:** Migration or rollback requires operator action but docs say "run migration" or omit rollback. **Hidden risk:** release cannot be recovered safely during incident. **Required professional action:** require migration and rollback procedure with expected outputs. **Route to:** `delivery-release-gate`, `release-rollback`. **Evidence required:** forward/rollback steps, verification query/command, owner.
- **Signal:** New alert, metric, SLO, dashboard, or operational dependency lacks runbook update. **Hidden risk:** missing runbook creates silent incident triage failure for on-call. **Required professional action:** write or update runbook before enabling alert/release. **Route to:** `reliability-observability-gate`, `observability`. **Evidence required:** alert trigger, triage steps, escalation path, validation output, and runbook owner.
- **Signal:** ADR, compliance, incident, or security evidence is requested after the decision or release. **Hidden risk:** audit trail is missing decision context, approval, or retention proof. **Required professional action:** capture evidence owner, timestamp, approval, exception, and residual risk before closure. **Route to:** `architecture-impact-reviewer`, `security-privacy-gate`. **Evidence required:** ADR/control/postmortem artifact, approval source, retention metadata, and evidence owner.

### Decision Tree: Documentation Required?

```
Does the change alter observable behavior for users, operators, or API consumers?
├── Yes → User guide / API docs update required
Does the change introduce or modify a breaking change?
├── Yes → Migration guide + deprecation notice required before release
Does the change add or modify an alert, SLO, or operational procedure?
├── Yes → Runbook update required before deployment
Does the change make an irreversible architecture decision?
├── Yes → ADR required before implementation
Does the change modify configuration keys, env vars, or defaults?
├── Yes → Config reference update required
Was there a customer-impacting incident or SEV?
├── Yes → Incident report + customer advisory/status page + postmortem summary required
Is the change regulated or audit-relevant?
├── Yes → Control mapping + evidence packet + owner/retention metadata required
None of the above → Document as no-change with rationale
```

## Risk Escalation Rules
- Escalate when a public API breaking change ships without a migration guide and active consumers exist.
- Escalate when a security posture change requires a public disclosure, CVE, or compliance advisory.
- Escalate when operational documentation for a new alert or monitoring path does not exist and the component is going to production.
- Escalate when a data migration script is undocumented and the rollback path requires manual database intervention.
- Escalate when documentation ownership is contested or unassigned and the release cannot proceed without resolution.
- Escalate when changelog or release notes omit a change that materially affects user behavior, billing, or data.
- Escalate when a customer-impacting incident lacks an approved communication cadence, status page decision, or postmortem publication owner.
- Escalate when compliance evidence lacks a control owner, evidence owner, exception owner, or retention period.

## Critical Details
- **Changelog entry categories** (follow Keep a Changelog standard): `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` — every category that applies must be present.
- **ADR status lifecycle**: `Proposed → Accepted → Deprecated → Superseded` — ADRs that are superseded must link to the superseding ADR.
- **Migration guide structure**: (1) Who is affected, (2) What changed, (3) Required action before upgrade, (4) Required action after upgrade, (5) Rollback instructions.
- **Runbook structure** (SRE standard): (1) Alert trigger condition, (2) Impact description, (3) Immediate triage steps, (4) Resolution steps, (5) Escalation path, (6) Post-incident action.
- **API documentation completeness**: Every endpoint must document all request parameters, all response codes (success and error), all error codes with meaning, and rate limiting behavior.
- **Config documentation**: Every environment variable must document: purpose, type, required/optional, default value, example value, and what happens if missing.
- **Deprecation notice requirements**: Declared sunset date, migration alternative, link to migration guide, affected version range.
- **Documentation review timing**: Documentation must be reviewed alongside code in the same pull request — post-release documentation is debt, not documentation.
- **Incident documentation set**: incident report, customer advisory, status page entry, postmortem summary, and corrective action tracking must use the same timeline and impact language. Conflicting timestamps or impact scopes create support and audit risk.
- **Compliance evidence metadata**: every evidence artifact needs control objective, evidence owner, control owner, approval source, freshness date, retention period, and exception owner when the control is not fully met.

### Anti-Examples

| Documentation Failure | Problem | Required Correction |
|---|---|---|
| `// See code for details` in user guide | Not documentation | Write the behavior in plain language for the target audience |
| Changelog: "Various bug fixes and improvements" | No behavioral information for consumers | List each fix with issue reference, behavior before/after |
| API endpoint added but OpenAPI spec not updated | Undiscovered contract | Update spec in same PR, block merge until updated |
| `API_KEY=your_key_here` in README | Placeholder, not documentation | Document purpose, format, where to obtain, rotation procedure |
| Breaking change shipped without migration guide | Breaks consumers | Write and link migration guide before merge |

## Failure Modes
- **Documentation drift causes wrong usage**: Users follow outdated documentation and trigger deprecated behaviors or fail to configure correctly — support burden increases.
- **Missing migration notes break consumer deployments**: A field is removed from an API response; consumers that read that field fail silently or crash — no migration guide was provided.
- **No runbook slows incident recovery**: A new alert fires in production; the on-call engineer has no triage steps and must reconstruct the diagnosis from memory under pressure.
- **ADR written retroactively loses value**: An architecture decision is documented after implementation — alternatives were not seriously considered because the decision was already irreversible.
- **Over-documenting internal implementation details**: Internal function names, database table names, and algorithm implementation details are documented publicly — refactoring becomes externally breaking.
- **Stale troubleshooting guide misleads**: A guide references a removed feature or deprecated endpoint — users follow it and the steps make the problem worse.
- **Security detail in public docs**: An internal service URL, secret key format, or error message that reveals infrastructure topology is published in documentation — an attacker uses it to plan targeted attacks.
- **Ownership gap**: A service transitions teams and the documentation is never updated to reflect the new owner — incident escalation goes to the wrong team.

## Reference Loading Policy
Do not load every reference by default. Treat references as targeted support selected by the router and the task risk.

- L1 changes: do not read references unless the task touches security, data, auth, external integration, performance, release, or irreversible behavior.
- L2 changes: read `references/capabilities/index.md` and only capability files explicitly selected by `change-forge-router`.
- L3 changes: read all selected capability references and `references/checklist.md` when present.
- L4/L5 changes: read all selected capability references, `references/checklist.md` when present, and domain extension references when selected.
- Selected capability reference path format: `references/capabilities/<capability-id>-<capability-name>.md`.

Examples:
- `42 idempotency-retry-design` -> `references/capabilities/42-idempotency-retry-design.md`
- `82 solution-optimality-evaluation` -> `references/capabilities/82-solution-optimality-evaluation.md`

## Output Contract
Return a documentation impact assessment with:
- **Mode selected**: Documentation mode and trigger signal that selected it.
- **Documentation matrix**: Each documentation artifact (README, API spec, runbook, ADR, changelog, migration guide, config reference) marked as: Updated / Not required (with rationale) / Outstanding (blocking).
- **Audience map**: Each updated artifact with its target audience and review owner.
- **Breaking change checklist**: Migration guide, deprecation notice, and consumer notification status.
- **Consumer impact report**: changed contract, known/unknown consumers, compatibility decision, generated-client impact, telemetry, rollout/rollback, and residual consumer risk.
- **Configuration policy documentation**: config scope, schema/type, defaults, validation/fail-fast behavior, feature flag lifecycle, kill switch behavior, test matrix, cleanup owner/date, and residual config risk.
- **Cleanup/deletion documentation**: target artifact, owner, removal condition, caller/runtime reference search, telemetry evidence, rollback path, cleanup issue, and residual deletion risk.
- **Architecture enforcement documentation**: rule list, tool choice, CI command, failure examples, generated-code exceptions, migration path, owner, and residual unenforced rule.
- **Operational readiness check**: Runbook and alert documentation completeness for new operational paths.
- **Incident documentation package**: Incident report, customer advisory, status page entry, postmortem summary, corrective action tracking, and publication/review owners.
- **Compliance evidence package**: Control objective, evidence artifact, control owner, evidence owner, exception owner, evidence freshness, and retention period.
- **Release notes draft**: Changelog entries for this change, categorized by Keep a Changelog standard.
- **Open items**: Documentation debt that is accepted but deferred, with owner and due date.
- **Boundary / no-docs rationale**: Docs explicitly not required only when no user, operator, integrator, developer, auditor, or release behavior changes.
- **Boundaries inspected**: code/schema/config/API/docs/runbook/changelog/ADR/release artifacts inspected or skipped with reason.
- **Professional judgment**: audience, artifact placement, not-required decisions, and blocking vs deferred doc debt.
- **Reuse and placement rationale**: existing doc location, template, spec, runbook, or changelog category reused; new doc placement justified.
- **Behavior preservation statement**: documented old behavior preserved or intentionally changed, with migration note when needed.
- **Validation evidence**: docs link check, generated spec, example command, rendered artifact, or not-verified disclosure.
- **Evidence limits**: what documentation evidence proves and does not prove about production behavior, consumer adoption, or audit sufficiency.
- **Residual risk and next gate**: deferred doc item, owner, due date, release block status, and handoff.

## Evidence Contract
Close a documentation gate only when all five canonical answers are concrete (answer schema: `agent-execution-discipline`). Treat docs as handoff evidence, not optional commentary.
- **Basis**: the code, schema, command, or config change that makes each documentation update necessary.
- **Files and boundaries inspected**: every documentation artifact in scope — README, API docs, ADR, migration notes, runbook, changelog, operator notes — each marked Updated, Not-required-with-rationale, or Outstanding.
- **Placement rationale**: why each update lands in the artifact and audience it does, and what changed, what did not, and how a reader verifies the change.
- **Validation commands**: the checks that prove the docs match reality — example/command re-run, schema or API-doc regeneration, link check — each with its outcome.
- **Documentation judgment and evidence limits**: mode selected, behavior preservation or no-docs decision, what evidence proves, what it does not prove, residual risk, and next gate.
- **Residual risk**: the deferred doc, the next owner, and the rollback or follow-up note that remains.

## Quality Gate
1. All user-facing behavior changes have updated user documentation or user-visible changelog entries.
2. All public or internal API contract changes have updated API documentation (OpenAPI spec or equivalent).
3. All breaking changes have migration guides published before the change ships.
4. All new operational paths (alerts, SLOs, procedures) have runbook coverage.
5. All irreversible architecture decisions have written ADRs.
6. All new configuration keys or environment variables have documented purpose, type, default, and failure behavior.
7. No documentation exposes secrets, credentials, or security-sensitive implementation details.
8. Documentation ownership is assigned for all changed artifacts.
9. Changelog entries are human-readable and audience-appropriate — not commit log dumps.
10. Documentation has been reviewed in the same pull request or release gate as the code change.
11. Customer-impacting incidents have incident report, customer advisory/status page decision, postmortem summary, and corrective action tracking.
12. Compliance evidence includes control, evidence artifact, owner, exception, freshness, and retention metadata.
13. The documentation closure states validation evidence (which examples, commands, or link checks ran) and residual risk; completion language is not used without that evidence.
14. Consumer-impacting contract changes have migration, deprecation, telemetry, rollout, and rollback documentation.
15. Runtime config and feature flags document typed schema, defaults, validation, owner, expiry, kill switch, rollout, rollback, and cleanup.
16. Cleanup/deletion work documents caller search, runtime/generated/reflection reference risk, telemetry proving unused, rollback path, and owner.
17. Architecture rules that are meant to persist have documented enforcement tooling and CI gate, or an explicit residual unenforced-rule decision.

## Handoff
- **delivery-release-gate** — when release notes, communication plans, or staged rollout documentation are required.
- **security-privacy-gate** — when documentation changes may inadvertently disclose security posture or require a security advisory.
- **reliability-observability-gate** — when runbook or alert documentation is incomplete for a new operational path.
- **failure-diagnosis** — when an incident report or postmortem summary needs verified timeline, root cause, or CAPA action evidence.
- **architecture-impact-reviewer** — when an ADR is required but the architecture decision has not yet been reviewed.
- **data-api-contract-changer** — when API documentation reveals a contract gap that must be resolved before the spec can be published.
- **consumer-impact-analysis** — when API, SDK, schema, event, public export, generated-client, mobile, web, or backend consumer impact is unknown.
- **configuration-runtime-policy** — when config keys, defaults, runtime switches, feature flags, kill switches, owner, expiry, or cleanup policy is unclear.
- **cleanup-deletion-governance** — when docs mention deprecated APIs, stale flags, fallbacks, compatibility branches, or deletion work without owner and removal evidence.
- **architecture-enforcement-tooling** — when architecture rules need import, cycle, export, dependency, lint, type-check, or CI enforcement documentation.

## Completion Criteria
Documentation impact is fully closed when every affected audience has accurate, reviewed documentation or an explicit no-change rationale; all breaking changes have migration guides; all new operational paths have runbooks; incident and compliance evidence artifacts have owner and retention metadata when applicable; no undocumented deprecations exist; and documentation ownership is assigned for every changed artifact.
