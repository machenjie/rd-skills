# rd-skills Documentation

Use this page as the map for both the installed rd-skills product and its
authoring repository. Installable artifacts come from `dist/`; `src/` is never
an installation source.

## Install And Complete A First Task

- [Quickstart](QUICKSTART.md): prepare the repository, choose a host and scope,
  preview, install, run doctor, and submit a first request.
- [Installation](INSTALLATION.md): supported hosts and scopes, default paths,
  build/install/upgrade/uninstall, backup boundaries, and recovery.
- [Usage](USAGE.md): copyable Direct Task, Analyzed Work, and review-only
  requests, plus expected interaction and handoff contents.
- [Scenario Showcase](SHOWCASE.md): generated routes and complete evidence
  obligations from the repository examples.
- [Routing examples](ROUTING_EXAMPLES.md): additional routing decisions.
- [Migration to the hookless architecture](MIGRATING_TO_HOOKLESS.md): legacy
  removal, compatibility, and rollback.

## Understand The System

- [Hookless architecture](HOOKLESS_ARCHITECTURE.md): product structure and
  non-intercepting execution model.
- [AI control boundaries](AI_CONTROL_BOUNDARIES.md): authority and enforcement
  limits.
- [Operating model](OPERATING_MODEL.md): task, evidence, and completion
  contracts.
- [Subagent model](SUBAGENT_MODEL.md): four roles, handoffs, and write
  serialization.
- [Runtime build](BUILD_PROFILES.md): the one 26-Skill top-level surface, JIT
  Layer 3 delivery, compatibility path, and manifests.
- [Marketplace](MARKETPLACE.md): how to use the source-derived discovery views.
- [Marketplace Catalog](MARKETPLACE_CATALOG.md): generated Skill inventory and
  navigation.

## Author Or Maintain Skills

- [Skill content governance](SKILL_CONTENT_GOVERNANCE.md): root/reference
  placement, review evidence, and validation ownership.
- [Skill authoring base standard](skill_authoring_standard/SKILL_AUTHORING_BASE_STANDARD.md)
- [Professional Skill authoring standard](skill_authoring_standard/PROFESSIONAL_SKILL_AUTHORING_STANDARD.md)
- [Foundation capability authoring standard](skill_authoring_standard/FOUNDATION_CAPABILITY_AUTHORING_STANDARD.md)
- [Domain extension authoring standard](skill_authoring_standard/DOMAIN_EXTENSION_AUTHORING_STANDARD.md)

Professional quality is defined separately from AI readability:

- [Skill professionalism base standard](skill_professionalism_standard/SKILL_PROFESSIONALISM_BASE_STANDARD.md)
- [Professionalism dimension rubric](skill_professionalism_standard/SKILL_PROFESSIONALISM_DIMENSION_RUBRIC.md)
- [Professionalism evaluation and governance](skill_professionalism_standard/SKILL_PROFESSIONALISM_EVALUATION_AND_GOVERNANCE.md)

## Validate, Interpret Evidence, And Release

- [Validation](VALIDATION.md): the canonical ordinary and formal command paths.
- [Quality model](QUALITY_MODEL.md): evidence types, limits, and quality levels.
- [Benchmarks](BENCHMARKS.md): routing, behavior, pressure, and code-generation
  evidence.
- [Scorecard](SCORECARD.md): handwritten evidence expectations, never generated
  status or a current-tree pass report.
- [Release](RELEASE.md): formal operator sequence, stop conditions, packaging,
  and release handoff limits.
- [Open-source readiness](OPEN_SOURCE_READINESS.md): publication metadata and
  repository checks.
- [Reports index](../reports/README.md): generated and captured report owners.
- [Agent-behavior eval](../evals/agent-behavior/README.md)
- [Code-generation eval](../evals/codegen/README.md)
- [Pressure eval](../evals/pressure/README.md)

The complete worked-example source is in the [examples index](../examples/README.md).
Generated reports and eval outputs are evidence snapshots; they do not own the
rules they measure.

## Contribute Or Get Help

- [Contributing](../CONTRIBUTING.md)
- [Governance](../GOVERNANCE.md)
- [Security policy](../SECURITY.md)
- [Support](../SUPPORT.md)
- [Code of Conduct](../CODE_OF_CONDUCT.md)
- [Changelog](../CHANGELOG.md)

Static checks, fixtures, builds, and simulated installation do not prove
real-host Profile startup, wall-clock performance, provider behavior,
production accuracy, or the installed user experience.
