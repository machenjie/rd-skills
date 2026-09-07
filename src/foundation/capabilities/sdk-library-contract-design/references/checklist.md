# SDK Library Contract Design Checklist

- Define exported symbols, public types, configuration keys, errors, lifecycle hooks, and generated operations.
- Classify the change as patch, minor, major, or internal-only with compatibility rationale.
- Pin generation source and generator version for generated clients.
- Review the affected public surface diff and any generated code diff.
- Define supported runtimes, package managers, server/API versions, and dependency floors.
- Provide runnable examples for primary usage and at least one error path.
- Run current consumer contract, fixture, or downstream smoke proof for the changed surface; add or change tests only for a material coverage gap.
- Map repository inspection, prior task evidence, and execution evidence for exports, generated output, package metadata, docs/examples, consumers, validators, and stale assumptions.
- Document deprecation, migration, removal version, and rollback or yanking policy.
- Verify package metadata, changelog, release notes, license, provenance, and security contact.
