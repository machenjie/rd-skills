# E2E Testing Checklist

- Select only critical journeys or high-risk branches.
- Include affected auth, permission denial, failure, and recovery paths.
- Use deterministic isolated test data and stable selectors.
- Avoid arbitrary sleeps and shared environment assumptions.
- Assert user-visible outcomes plus durable side effects where relevant.
- Capture trace, screenshot, video, logs, or network evidence for failures.
