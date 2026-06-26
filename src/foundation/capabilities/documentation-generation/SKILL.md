---
name: documentation-generation
description: Produces documentation that reflects actual behavior, API contracts, migrations, configuration, operations, and release impact.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "80"
changeforge_version: 0.1.0
---

# Mission

Produce **source-grounded, audience-appropriate, release-aware documentation** that reflects actual behavior, contracts, configuration, migrations, operations, validation evidence, and residual risk - so users, operators, reviewers, auditors, and future implementers can act without guessing or relying on stale agent memory.

# When To Use

Use this capability when generating, updating, reviewing, or deciding not to update README content, API docs, SDK notes, runbooks, ADRs, changelogs, migration guides, configuration references, troubleshooting guides, operational procedures, release notes, compliance evidence, or durable handoff docs. Use it when a change affects what a reader must know, when docs appear stale against current source, or when an agent plans to summarize implementation behavior for future execution.

# Do Not Use When

Do not use this capability for temporary AI context transfer, speculative design copy, marketing copy, tutorial prose detached from the repository, or claims that cannot be traced to source behavior, schema, config, command output, tests, accepted decision records, or release evidence. Do not document secrets, private credentials, production-only topology, or unsafe operational shortcuts.

# Stage Fit

Use during requirement and planning when documentation is an explicit deliverable; during coding/review when behavior, API, config, migration, or operational changes need docs alignment; during release when changelog, migration, runbook, or customer/support communication is required; and during handoff when validation evidence, residual risk, and future-reader instructions must be durable. Hand off when the primary work is temporary context packaging, API contract design, release rollback design, incident diagnosis, or implementation review rather than documentation closure.

# Non-Negotiable Rules

- **Docs describe what is true now.** Every documented behavior, command, config, API field, error code, migration step, or operational procedure must trace to current source, schema, generated artifact, test, command output, accepted decision, or release plan.
- **Audience controls depth.** Operator runbooks need trigger, action, expected output, escalation, and rollback; API docs need request/response/error semantics; contributor docs need setup and validation; release notes need reader-impact language.
- **No unsupported claims.** Mark deprecated, experimental, unsupported, environment-specific, unverified, or inferred behavior clearly. Do not turn project memory, prior agent summaries, or stale docs into facts without current-source confirmation.
- **Docs change with behavior.** If stale docs would mislead users, operators, API consumers, auditors, or future implementers, update or remove them in the same change or record an explicit documentation-debt owner and release consequence.
- **Examples are contracts.** Code snippets, CLI commands, request/response examples, and config blocks must be executable, generated, or explicitly marked illustrative with evidence limits.
- **Migration and rollback language is mandatory when versions diverge.** Breaking changes, data migrations, deprecations, feature flags, config defaults, and operational rollouts must state compatibility, order, rollback, forward-fix, and owner.

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| No-docs decision | Internal refactor, test-only change, or cosmetic edit claims no durable docs change. | Prove no audience, contract, operator, release, or auditor behavior changed. | Changed files, affected audience scan, existing docs searched, no-change rationale. | `change-impact-analyzer`, `code-review` | Changelog noise for invisible changes. |
| User or contributor docs | Feature, setup, workflow, validation, CLI, SDK, or contributor behavior changes. | Put accurate instructions where the reader already looks. | Source paths, current behavior, reader task, examples verified or marked illustrative. | `context-packaging`, `acceptance-standard-definition` | Internal implementation detail. |
| API/config/contract docs | Endpoint, event, schema, error, env var, feature flag, or public export changes. | Keep contract docs synchronized with authoritative definitions. | Spec/schema/config source, before/after semantics, compatibility and consumer note. | `api-contract-design`, `version-compatibility`, `contract-testing` | Runbook unless operational behavior changed. |
| Migration/release docs | Migration, deprecation, rollout, rollback, release note, or version skew exists. | Preserve safe upgrade and rollback instructions before release. | Migration order, rollback/forward-fix, release impact, owner, validation command. | `release-rollback`, `delivery-release-gate` | User guide when only operators are affected. |
| Operational/runbook docs | Alert, SLO, dashboard, troubleshooting, incident response, or support flow changes. | Keep on-call and support actions executable under pressure. | Trigger, impact, triage, expected output, escalation path, signal owner. | `observability`, `reliability-observability-gate` | API migration docs unless contract changed. |
| ADR/compliance/handoff evidence | Architecture decision, audit control, incident, exception, residual risk, or cross-session handoff. | Preserve decision integrity, evidence ownership, freshness, and retention. | Decision source, alternatives, approval, evidence owner, retention, risk limits. | `architecture-impact-reviewer`, `security-privacy-gate`, `agent-execution-discipline` | Marketing or broad narrative. |

# Industry Benchmarks

Anchor on docs-as-code, OpenAPI/AsyncAPI contract documentation, Keep a Changelog, RFC 7807 error documentation, runbook/SRE procedure standards, ADR traceability, migration-guide structure, compliance evidence ownership, and Google developer-documentation clarity. Keep this body focused on routing, evidence, and closure; load [references/checklist.md](references/checklist.md) for the compact documentation-generation checklist and use `examples/example-output.md` when output shape is unclear in source-authoring context.

# Selection Rules

Select this capability when durable documentation or an evidence-backed no-docs decision is primary. Prefer `context-packaging` for temporary AI task context, `change-documentation-gate` for product-level documentation impact closure, `api-contract-design` when the contract itself is not yet defined, `release-rollback` when rollback mechanics are unresolved, `observability` when signals/runbooks are not yet designed, and `code-review` when docs and implementation appear to disagree.

# Risk Escalation Rules

Escalate when docs describe public APIs, auth/security posture, privacy/compliance obligations, migrations, rollback, production configuration, incident procedures, customer-visible release impact, or operator recovery. Escalate when examples expose secrets, when docs conflict with source, when generated docs are accepted without validation, when project memory is used as fact, or when a release depends on documentation that has no owner.

# Proactive Professional Triggers

- **Signal:** A behavior, API, config, migration, or release change lands with no docs touched and no no-docs rationale. **Hidden risk:** affected readers discover the change by failure. **Required professional action:** produce documentation matrix or no-change proof. **Route to:** `change-documentation-gate`, `quality-test-gate`. **Evidence required:** affected audience, searched docs, updated/not-required decision, owner.
- **Signal:** An API example, CLI command, setup step, or config block is copied from old docs. **Hidden risk:** plausible stale instructions become executable misinformation. **Required professional action:** rerun, regenerate, or mark illustrative with limits. **Route to:** `validation-broker`, `contract-testing`. **Evidence required:** command/test/spec output or not-verified disclosure.
- **Signal:** Agent memory or previous handoff says docs are current. **Hidden risk:** stale memory hides current source drift. **Required professional action:** confirm against current source, graph-selected files, tests, and docs before reuse. **Route to:** `project-memory-governance`, `repository-graph-analysis`. **Evidence required:** memory accepted/rejected, inspected current paths, freshness limits.
- **Signal:** Release notes summarize "misc fixes" or hide breaking/operational impact. **Hidden risk:** users, support, and operators cannot plan adoption or rollback. **Required professional action:** write reader-impact categories and migration/rollback notes. **Route to:** `delivery-release-gate`, `release-rollback`. **Evidence required:** changelog category, affected audience, upgrade action, rollback/forward-fix.
- **Signal:** Runbook or incident docs lack expected outputs or escalation. **Hidden risk:** on-call cannot distinguish success from failure under pressure. **Required professional action:** add trigger, triage, expected result, failure indicator, escalation, and owner. **Route to:** `reliability-observability-gate`, `observability`. **Evidence required:** alert/signal, runbook path, validation method, owner.
- **Signal:** Public docs mention secrets, internal hostnames, security control internals, production identifiers, or real user data. **Hidden risk:** documentation creates an exposure path. **Required professional action:** redact or re-scope the doc and run security review. **Route to:** `security-privacy-gate`, `secret-configuration-security`. **Evidence required:** redaction decision, safe placeholder, residual risk.

# Critical Details

- **Documentation is an operational artifact.** Inaccurate docs can be as harmful as broken code because they direct real user, support, operator, and auditor behavior.
- **Repository graph selects evidence; it is not evidence by itself.** Use graph/context signals to find source, owners, docs, examples, tests, and generated artifacts, then inspect current files directly.
- **Project memory is experience input.** Prior decisions, fragile docs, and repeated failures may guide review, but source facts require current evidence.
- **Generated examples create compatibility promises.** If an example cannot be verified, state what it illustrates and what it does not prove.
- **No-docs is a documented decision.** A no-docs outcome must identify the audiences considered and why no durable artifact changes.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 routing, evidence, and output rules. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete documentation update. Use `examples/example-output.md` in source-authoring context only when a caller needs a sample documentation update plan. Do not load references for pure routing or trivial wording changes where the output contract and quality gate are sufficient.

# Anti-Examples

| Documentation failure | Problem | Corrected approach |
| --- | --- | --- |
| "See code for details" in a user guide | Forces readers to infer behavior from implementation. | Document the behavior for the reader and cite source evidence. |
| Changelog says "various fixes" | Hides behavior, migration, or support impact. | Categorize each material reader impact. |
| API example not regenerated after schema change | Consumers copy a stale contract. | Regenerate or verify against the authoritative schema/test. |
| Runbook says "restart service" | No trigger, expected output, or escalation. | Add preconditions, action, success signal, failure signal, escalation. |
| README includes a real token-shaped value | Secret-like data leaks through docs. | Use safe placeholder and secret-source guidance. |

# Failure Modes

- Docs describe intended behavior that the code does not implement.
- API examples drift from current schema, field defaults, rate limits, or error codes.
- Migration docs omit order, old/new compatibility, rollback, or forward-fix constraints.
- Configuration docs omit default, required/optional state, validation behavior, unsafe values, or owner.
- Release notes hide breaking changes, operational impact, customer-visible behavior, or support burden.
- Runbooks lack trigger, expected output, failure indicator, escalation, or verification method.
- Agent handoff docs over-claim validation or omit residual risk and stale evidence.

# Output Contract

Return a documentation decision or update plan with:

- `mode_selected` (no-docs, user/contributor docs, API/config/contract docs, migration/release docs, operational/runbook docs, ADR/compliance/handoff evidence)
- `audience_map` (reader groups, decisions they must make, depth required, owner/reviewer)
- `artifact_matrix` (README, API spec, SDK docs, runbook, ADR, changelog, migration guide, config reference, troubleshooting, release notes: updated/not required/outstanding with rationale)
- `source_evidence` (current code, schema, generated artifact, config, command, test, decision record, release plan, graph-selected path, or memory input with fact class and freshness)
- `behavior_summary` (what changed, what did not, old behavior preserved or intentionally changed)
- `contract_and_config_impact` (API fields, errors, env vars, feature flags, defaults, validation, compatibility)
- `migration_and_release_impact` (upgrade order, rollback/forward-fix, deprecation, changelog category, consumer/support communication)
- `operational_impact` (alerts, SLOs, runbooks, troubleshooting, expected outputs, escalation)
- `security_privacy_review` (secrets/PII/security detail exposure checked or explicitly not applicable)
- `graph_memory_execution_coupling` (repository graph paths inspected, project memory accepted/rejected, validation commands mapped to docs claims)
- `verification_method` (link check, generated spec, command/example run, schema diff, test, rendered artifact, or not-verified disclosure)
- `stale_doc_risks` (contradicted sections, unverified examples, deferred debt, owner, due date, release consequence)
- `handoff_boundaries` (what belongs to docs, API contract, release, reliability/runbook, security/privacy, or implementation review)
- `evidence_limits` (what the docs evidence proves and does not prove about production behavior, consumer adoption, audit sufficiency, or runtime correctness)

# Evidence Contract

- **Repository evidence:** name docs, source files, schemas, config, tests, generated artifacts, and release/decision records inspected; if a source is not inspected, mark the claim as unverified.
- **Graph and memory evidence:** graph and memory can identify likely docs, owners, callers, or stale areas, but current files and validation must confirm factual claims.
- **Execution evidence:** every executable command, snippet, API example, config default, migration step, or runbook action maps to a validator, command output, regenerated artifact, manual review, or residual risk.
- **Boundary evidence:** separate durable docs from temporary context packages; separate contract definition from contract documentation; separate release mechanics from release notes; separate source behavior from inferred explanation.
- **Safety evidence:** docs must not expose secrets, credentials, production PII, private topology, exploit detail beyond audience need, or unsafe operational shortcuts.

# Benchmark Coverage

Professional documentation generation covers source truth, audience fit, artifact placement, contract/config accuracy, migration and rollback clarity, operational actionability, security/privacy redaction, graph/memory freshness, execution validation, ownership, and residual-risk disclosure. A fluent summary without evidence and verification is incomplete.

# Routing Coverage

Route here when the primary question is what durable documentation to produce, update, verify, or explicitly decline. Hand off to `context-packaging` for temporary agent context, `change-documentation-gate` for product-level doc impact closure, `api-contract-design` or `data-api-contract-changer` for unresolved contracts, `delivery-release-gate` or `release-rollback` for rollout mechanics, `reliability-observability-gate` for runbook and alert design, `security-privacy-gate` for disclosure/privacy risk, and `code-review` when source and docs disagree.

# Quality Gate

The documentation decision is complete only when:

1. Every documented behavior, command, API field, config value, migration step, and operational action traces to current source or an explicit accepted decision.
2. The target audience and artifact placement are named for every updated or deferred doc.
3. Existing docs were searched for stale or contradicted sections in the affected area.
4. Examples, snippets, commands, schemas, and generated docs are run, regenerated, or marked not verified with a reader-safe limitation.
5. API, config, and schema references match authoritative definitions, including defaults, errors, and compatibility notes.
6. Breaking changes, deprecations, migrations, and feature flags include migration, rollback, forward-fix, owner, and release timing.
7. Operational docs include trigger, impact, triage, expected output, failure signal, escalation, and verification method.
8. No secrets, credentials, production PII, private topology, or unsafe shortcuts are exposed.
9. Project memory and prior agent summaries are confirmed against current source or labeled stale/unverified.
10. Every updated artifact has an owner, review path, validation method, residual-risk statement, and stale-doc trigger.
11. No-docs decisions list the audiences and artifacts considered, with evidence-backed rationale.
12. Deferred documentation debt names owner, due date, release consequence, and whether it blocks handoff.

# Used By

- change-documentation-gate

# Handoff

Hand off to `change-documentation-gate` for product-level documentation impact closure; `api-contract-design` or `data-api-contract-changer` for unresolved API/schema semantics; `release-rollback` and `delivery-release-gate` for rollout, rollback, and release-note mechanics; `reliability-observability-gate` for runbook, alert, SLO, and incident procedure design; `security-privacy-gate` when documentation may expose sensitive data or security posture; `context-packaging` when the need is temporary agent context rather than durable documentation; and `code-review` when documentation contradicts implementation.

# Completion Criteria

The capability is complete when **documentation truthfully reflects current behavior and release impact, is placed for the right audience, cites or maps to source evidence, verifies executable examples or labels them safely, preserves graph/memory freshness limits, avoids sensitive exposure, and states owner, validation method, stale-doc triggers, and residual risk without speculative or unsafe guidance**.
