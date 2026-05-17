# Frontend Testing Checklist

- Identify the user-visible behavior changed by the work.
- Cover core happy path, negative path, and recovery path.
- Add role and permission-state coverage for protected UI and actions.
- Test loading, empty, error, disabled, success, timeout, and stale states where relevant.
- Verify form validation and duplicate-submit behavior where forms are involved.
- Mock APIs at stable contract boundaries.
- Avoid tests that only assert internal component implementation details.
- Include accessibility checks for labels, focus, keyboard flow, and error announcements.
- Choose unit, integration, or E2E level based on risk and coordination needs.
- Define flake controls, fixtures, and required review evidence.
