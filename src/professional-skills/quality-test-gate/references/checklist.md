# Quality Checklist

- Map each acceptance criterion to evidence.
- Choose unit tests for pure logic and edge cases.
- Choose integration tests for persistence, services, permissions, and jobs.
- Choose contract tests for API and external boundaries.
- Choose E2E tests for critical user flows.
- Include migration, rollback, and data repair tests when needed.
- Review fixture realism and mock boundaries.
- Consume exact commands, expected signals, and combined coverage from `targeted-validation-selection`; keep proof admissibility and pass criteria with this gate.
- Record residual risk and manual verification.
