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
None of the above → Document as no-change with rationale
```

## Risk Escalation Rules
- Escalate when a public API breaking change ships without a migration guide and active consumers exist.
- Escalate when a security posture change requires a public disclosure, CVE, or compliance advisory.
- Escalate when operational documentation for a new alert or monitoring path does not exist and the component is going to production.
- Escalate when a data migration script is undocumented and the rollback path requires manual database intervention.
- Escalate when documentation ownership is contested or unassigned and the release cannot proceed without resolution.
- Escalate when changelog or release notes omit a change that materially affects user behavior, billing, or data.

## Critical Details
- **Changelog entry categories** (follow Keep a Changelog standard): `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security` — every category that applies must be present.
- **ADR status lifecycle**: `Proposed → Accepted → Deprecated → Superseded` — ADRs that are superseded must link to the superseding ADR.
- **Migration guide structure**: (1) Who is affected, (2) What changed, (3) Required action before upgrade, (4) Required action after upgrade, (5) Rollback instructions.
- **Runbook structure** (SRE standard): (1) Alert trigger condition, (2) Impact description, (3) Immediate triage steps, (4) Resolution steps, (5) Escalation path, (6) Post-incident action.
- **API documentation completeness**: Every endpoint must document all request parameters, all response codes (success and error), all error codes with meaning, and rate limiting behavior.
- **Config documentation**: Every environment variable must document: purpose, type, required/optional, default value, example value, and what happens if missing.
- **Deprecation notice requirements**: Declared sunset date, migration alternative, link to migration guide, affected version range.
- **Documentation review timing**: Documentation must be reviewed alongside code in the same pull request — post-release documentation is debt, not documentation.

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
- **Documentation matrix**: Each documentation artifact (README, API spec, runbook, ADR, changelog, migration guide, config reference) marked as: Updated / Not required (with rationale) / Outstanding (blocking).
- **Audience map**: Each updated artifact with its target audience and review owner.
- **Breaking change checklist**: Migration guide, deprecation notice, and consumer notification status.
- **Operational readiness check**: Runbook and alert documentation completeness for new operational paths.
- **Release notes draft**: Changelog entries for this change, categorized by Keep a Changelog standard.
- **Open items**: Documentation debt that is accepted but deferred, with owner and due date.

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

## Handoff
- **delivery-release-gate** — when release notes, communication plans, or staged rollout documentation are required.
- **security-privacy-gate** — when documentation changes may inadvertently disclose security posture or require a security advisory.
- **reliability-observability-gate** — when runbook or alert documentation is incomplete for a new operational path.
- **architecture-impact-reviewer** — when an ADR is required but the architecture decision has not yet been reviewed.
- **data-api-contract-changer** — when API documentation reveals a contract gap that must be resolved before the spec can be published.

## Completion Criteria
Documentation impact is fully closed when every affected audience has accurate, reviewed documentation or an explicit no-change rationale; all breaking changes have migration guides; all new operational paths have runbooks; no undocumented deprecations exist; and documentation ownership is assigned for every changed artifact.
