---
name: sdk-library-contract-design
description: "`analysis-agent`/`task-agent`/`review-agent`: use when SDK/library APIs, semver, compatibility, deprecation, or migration changes; skip without library-contract impact."
---

# sdk-library-contract-design

## Registry Trigger

**Use when**

- SDK library generated client package public API internal library semver deprecation examples migration consumer contract tests publication

**Do not use when**

- no task-local sdk library contract design decision is required

## Skill Role

Define the consumer contract, ecosystem-specific compatibility classification, generated-client lineage, adoption path, and consumer proof. Exclude package resolution, release mutation, and documentation publication.

## High-Value Rules

- **Own distributed contract encoding.** `module-boundary-design` retains internal responsibility, state, and dependencies, while `extensibility-design` retains host registration, negotiation, isolation, and lifecycle; from first distribution, this capability owns exported compatibility, migration, and consumer proof.
- **Inventory the consumed surface before classifying change.** Include exported symbols and types, defaults, errors, configuration, lifecycle behavior, extension points, generated operations, runtime floors, package metadata, and observable side effects.
- **Derive compatibility from real consumers and ecosystem semantics.** Classify source, binary, wire, behavioral, packaging, and runtime impact using current support policy and language rules rather than a universal version label.
- **Treat types, errors, and defaults as behavior.** Check compilation, reflection, exhaustive matching, exception handling, serialization, overload resolution, and implicit default changes even when the nominal signature still parses.
- **Make generated output reproducible.** Bind source specification, generator and templates, configuration, and generated artifacts to identifiable versions; review semantic drift separately from mechanical churn.
- **Design mixed-version adoption.** Select a migration strategy only with explicit removal evidence and rollback limits.
- **Prove the packed consumer experience.** Build representative consumers against the distributable artifact and exercise affected calls, errors, configuration, and generated code across supported environments.
- **Expose publication and supply-chain consequences.** Hand signing, provenance, registry mutation, dependency floors, licensing, yank, and release authority to the relevant delivery, package, security, and documentation owners.

## Anti-Patterns

- Infer compatibility from declaration diff alone while defaults, errors, packaging, generated output, or runtime behavior change.
- Assume internal consumers upgrade atomically, or schedule removal from author preference without current usage evidence.
- Validate examples or fixture consumers against source internals instead of the artifact consumers receive.

## Stop Conditions

Escalate when the public surface or supported consumers are unknown, ecosystem compatibility rules conflict, generated lineage is irreproducible, or a long-lived consumer lacks an adoption path. Also escalate when rollback would strand persisted or wire data, or publication changes credentials, licensing, security, or irreversible registry state.

## Output Contract

- library contract decision with consumed surface, compatibility classification, generated lineage, mixed-version adoption, consumer proof, release handoffs, proof limits, and residual owners

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | versioning generation compatibility or release mechanisms remain undecided | ecosystem policy and consumer contract select one release path | task-agent, review-agent, analysis-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | change affects exports types defaults runtimes generation consumers or deprecation | public package and generated surfaces remain unchanged | task-agent, review-agent, analysis-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | semver generation consumer or provenance claims need fresh artifacts | API diffs fixture consumers and packed examples prove each claim | task-agent, review-agent, analysis-agent | evidence-record, proof-limit, residual-risk |
