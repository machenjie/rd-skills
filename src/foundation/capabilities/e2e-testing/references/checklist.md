# E2E Testing Checklist

- Select only critical journeys or high-risk branches.
- Include affected auth, permission denial, failure, and recovery paths.
- Use deterministic isolated test data and stable selectors.
- Avoid arbitrary sleeps and shared environment assumptions.
- Assert user-visible outcomes plus durable side effects where relevant.
- Capture trace, screenshot, video, logs, or network evidence for failures.
- Confirm repository graph, project memory, prior CI output, or agent claims against current source before reuse.
- Record validation command, exit code, artifact path, freshness, and what the E2E evidence does not prove.
