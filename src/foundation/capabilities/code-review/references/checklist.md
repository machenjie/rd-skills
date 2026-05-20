# Code Review Checklist

- Check changed behavior against requirements and contracts.
- Check architecture boundaries and ownership rules.
- Check security, permissions, input validation, and secret handling.
- Check error handling, logging, and failure behavior.
- Check collection/buffer/cache/batch/page growth limits and oversized-input behavior.
- Check reusable client/pool lifecycle, connection reuse, response/stream/cursor cleanup, and long-lived handle disposal.
- Check dependency use, generated APIs, config keys, and commands against project reality.
- Check tests for meaningful behavior, edge cases, and regressions.
- Check naming and maintainability only after material risk.
- Report findings with severity, evidence, impact, and remediation.
