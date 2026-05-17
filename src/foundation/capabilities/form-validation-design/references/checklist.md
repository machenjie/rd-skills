# Form Validation Design Checklist

- List fields, required rules, formats, ranges, dependencies, and business rules.
- Identify backend validation authority for every rule.
- Treat frontend validation as UX feedback only.
- Define validation timing for change, blur, submit, async check, and server response.
- Cancel or ignore stale async validation results.
- Prevent duplicate submits and define idempotency where side effects are possible.
- Preserve user input on validation failure, timeout, or retryable error.
- Map backend errors to field-level or form-level messages.
- Define partial failure behavior for batch or multi-step submissions.
- Add tests for invalid input, async validation, duplicate submit, and partial failure recovery.
