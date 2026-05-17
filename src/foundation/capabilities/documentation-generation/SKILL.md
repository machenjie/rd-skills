---
name: documentation-generation
description: Produces documentation that reflects actual behavior, API contracts, migrations, configuration, operations, and release impact.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "80"
changeforge_version: 0.1.0
---

# Mission

Keep documentation aligned with shipped behavior so users, operators, reviewers, and future implementers can trust it.

# When To Use

Use this capability when generating or updating README content, API docs, runbooks, ADRs, changelogs, migration docs, configuration references, operational procedures, or release notes.

# Do Not Use When

Do not use this capability to write speculative docs, marketing copy, tool tutorials, or claims that are not supported by source behavior or release decisions.

# Non-Negotiable Rules

- Docs must reflect actual behavior, API contracts, migrations, configuration, operations, and release impact.
- Verify documentation against source files, schemas, commands, configs, tests, or accepted decisions.
- Mark unsupported, deprecated, experimental, or environment-specific behavior clearly.
- Update docs in the same change as behavior when stale docs would mislead users or operators.
- Include migration and rollback impact when behavior changes across versions.
- Do not document secrets, private credentials, or unsafe operational shortcuts.

# Industry Benchmarks

Use docs-as-code, API contract documentation, changelog discipline, runbook accuracy, ADR traceability, migration guides, configuration references, and release communication standards as benchmarks.

# Selection Rules

Select this capability when durable documentation is primary. Prefer context-packaging for temporary AI task context, release-rollback for release recovery plans, and api-contract-design when the API contract itself is still being defined.

# Risk Escalation Rules

Escalate when docs describe security behavior, compliance obligations, migrations, operational recovery, public APIs, breaking changes, production configuration, or customer-visible release impact.

# Critical Details

Documentation becomes harmful when it is plausible but false. Generated docs must cite or trace to real behavior. Operational docs should include owners and verification signals. API docs must match schemas and examples. Migration docs must name compatibility, order, rollback, and forward-fix expectations.

# Failure Modes

- Docs describe intended behavior that the code does not implement.
- API examples drift from current schema or error codes.
- Migration docs omit rollback and compatibility constraints.
- Configuration docs omit defaults, required values, or unsafe values.
- Release notes hide operational impact or breaking changes.

# Output Contract

Return a documentation update plan with: target audience, affected docs, source evidence, behavior summary, API or config changes, migration impact, operational impact, release impact, examples to update, verification method, owner, and stale-doc risks.

# Quality Gate

The documentation is complete only when it is source-backed, audience-appropriate, and accurate enough to guide operation, integration, migration, and review.

# Used By

- change-documentation-gate

# Handoff

Hand off to api-contract-design for unresolved contract details, release-rollback for rollout and rollback language, observability for runbook signals, or code-review when docs and implementation disagree.

# Completion Criteria

The capability is complete when documentation truthfully reflects current behavior and release impact without speculative or unsafe guidance.
