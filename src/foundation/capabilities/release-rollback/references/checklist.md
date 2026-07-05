# Release Rollback Checklist

- Identify every changed surface: code, config, data, flags, jobs, caches, and integrations.
- Define release order, validation checkpoints, and stop conditions.
- Define rollback trigger thresholds and decision owner.
- Verify mixed-version compatibility.
- Provide migration rollback or forward-fix strategy.
- Define feature flag defaults, owners, and emergency controls.
- Define external integration reversal or mitigation steps.
- Include post-release monitoring and communication path.
- Reconcile repository graph, project memory, generated docs, prior runbooks, and pipeline output with current release evidence.
- Map every rollback action to a validator, monitor, query, manual check, owner approval, or named residual risk.
