# Example Output

```markdown
## Project Initialization Plan

Structure:
- src/app: application entry and composition root.
- src/domain: business rules with no infrastructure dependency.
- src/adapters: persistence, provider, and transport integrations.
- tests/unit: domain and utility behavior.
- tests/integration: adapter and boundary behavior.
- docs: operational and contributor docs.
- deploy: environment-neutral deployment assets.

Configuration:
- Runtime values come from documented environment variables.
- Example config uses placeholders only.

Quality gates:
- format, lint, unit tests, integration tests, build, and package validation.
```
