# CI/CD Checklist

- Define pipeline triggers and required branch or merge checks.
- Include build, lint, tests, and relevant security checks.
- Produce traceable immutable artifacts.
- Promote artifacts rather than rebuilding differently per environment.
- Protect deployment credentials and redact logs.
- Define environment gates, approvals, and emergency exception policy.
- Define failure policy for required, warning, and flaky checks.
- Include rollback hooks and post-deploy verification.
