# Example Output

```markdown
## CI/CD Plan

Stages:
- validate: format, lint, unit tests.
- verify: integration tests, dependency scan, build.
- package: create versioned image and SBOM.
- deploy staging: promote packaged artifact and run smoke checks.
- deploy production: approval gate, canary, post-deploy checks.

Failure policy:
- Build, test, lint, and high-severity security findings block promotion.
- Flaky check waiver requires owner, expiry, and tracking issue.

Artifacts:
- One signed image promoted through all environments.
```
