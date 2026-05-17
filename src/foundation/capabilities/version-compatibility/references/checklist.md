# Version Compatibility Checklist

- Identify API, schema, event, config, and behavior surfaces affected.
- Build old-producer to new-consumer and new-producer to old-consumer matrix.
- Check field additions, removals, renames, enum values, defaults, and validation changes.
- Check semantic behavior changes, timing changes, and error code changes.
- Define versioning, staged rollout, compatibility bridge, or breaking-change approval.
- Define deprecation window, telemetry, and removal criteria.
- Define rollback behavior and mixed-version deployment assumptions.
- Verify unknown or external consumers are accounted for.
- Define contract tests or compatibility fixtures.
