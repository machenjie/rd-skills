# rd-skills Documentation

New to rd-skills? Use one path:

1. [README](../README.md) — understand the value and install.
2. [Quickstart](QUICKSTART.md) — verify setup and run a first task.
3. [Usage](USAGE.md) — use natural-language requests every day.

You do not need the maintainer documents below to use rd-skills.

## Installation and help

- [Advanced Installation & Recovery](INSTALLATION.md): supported tools, scopes, exact paths, previews, conflicts, backups, upgrade, uninstall, packages, and recovery.
- [Migrating older installations](MIGRATING_TO_HOOKLESS.md): historical installation cleanup, backup behavior, interruption recovery, and rollback.
- [Support](../SUPPORT.md): where to go and what redacted information to include.

## Understand the system

- [Hookless architecture](HOOKLESS_ARCHITECTURE.md): product structure and non-intercepting execution model.
- [AI control boundaries](AI_CONTROL_BOUNDARIES.md): authority and host-enforcement limits.
- [Operating model](OPERATING_MODEL.md): task, verification, and completion contracts.
- [Subagent model](SUBAGENT_MODEL.md): execution roles, handoffs, and write serialization.
- [Runtime build](BUILD_PROFILES.md): build composition, compatibility paths, and generated manifests.
- [Scenario Showcase](SHOWCASE.md): generated scenarios and their engineering obligations.

The complete worked-example source is in the [examples index](../examples/README.md). Generated documents are projections of their owning sources and must not be edited by hand.

## Discover or author Skills

- [Marketplace](MARKETPLACE.md): source-derived discovery views.
- [Marketplace Catalog](MARKETPLACE_CATALOG.md): generated Skill inventory and navigation.
- [Skill content governance](SKILL_CONTENT_GOVERNANCE.md): content placement, review evidence, and validation ownership.
- [Skill authoring base standard](skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md)
- [Professional Skill authoring standard](skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md)
- [Foundation capability authoring standard](skill_authoring_standard/FOUNDATION_CAPABILITY_AUTHORING_STANDARD.md)
- [Domain extension authoring standard](skill_authoring_standard/DOMAIN_EXTENSION_AUTHORING_STANDARD.md)

Professional quality and AI readability have separate owners:

- [Skill professionalism base standard](skill_professionalism_standard/SKILL_PROFESSIONALISM_BASE_STANDARD.md)
- [Professionalism dimension rubric](skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md)
- [Professionalism evaluation and governance](skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md)

## Validate and release

- [Validation](VALIDATION.md): canonical development, full-regression, and formal command paths.
- [Quality model](QUALITY_MODEL.md): evidence types, limits, and quality levels.
- [Benchmarks](BENCHMARKS.md): routing, behavior, pressure, and code-generation evidence.
- [Scorecard](SCORECARD.md): handwritten evidence expectations.
- [Release](RELEASE.md): operator sequence, stop conditions, packaging, and release limits.
- [Open-source readiness](OPEN_SOURCE_READINESS.md): publication metadata and repository checks.
- [Reports index](../reports/README.md): generated and captured report owners.
- [Agent-behavior eval](../evals/agent-behavior/README.md)
- [Code-generation eval](../evals/codegen/README.md)
- [Pressure eval](../evals/pressure/README.md)

## Project policies

- [Contributing](../CONTRIBUTING.md)
- [Governance](../GOVERNANCE.md)
- [Security policy](../SECURITY.md)
- [Support](../SUPPORT.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Changelog](../CHANGELOG.md)

This repository installs generated artifacts from `dist/`; `src/` is never an installation source.

Static panel evidence does not prove real-host Profile startup, wall-clock performance, provider behavior, production accuracy, or installed user experience.
