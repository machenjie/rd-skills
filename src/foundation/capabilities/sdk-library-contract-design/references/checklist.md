# SDK Library Contract Design Checklist

- Define exported symbols, public types, configuration keys, errors, lifecycle hooks, and generated operations.
- Classify the change as patch, minor, major, or internal-only with compatibility rationale.
- Pin generation source and generator version for generated clients.
- Review public surface diff and generated code diff.
- Define supported runtimes, package managers, server/API versions, and dependency floors.
- Provide runnable examples for primary usage and at least one error path.
- Add consumer contract tests, fixture projects, or downstream smoke tests.
- Document deprecation, migration, removal version, and rollback or yanking policy.
- Verify package metadata, changelog, release notes, license, provenance, and security contact.
