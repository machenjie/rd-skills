# Form Validation Design Checklist

- Select mode: basic field contract, async validation, side-effecting submit, error mapping, multi-step/bulk, or security-sensitive form.
- Inspect current form, backend schema/handler, API error contract, tests, stories, repository graph, project memory, and validation freshness.
- Record graph/memory/trajectory assumptions only when current source and validation confirm them.
- List fields, required rules, formats, ranges, dependencies, and business rules.
- Identify backend validation authority for every rule.
- Treat frontend validation as UX feedback only.
- Define validation timing for change, blur, submit, async check, and server response.
- Cancel or ignore stale async validation results.
- Prevent duplicate submits and define idempotency where side effects are possible.
- Specify CSRF/session protection for browser mutation forms.
- Preserve user input on validation failure, timeout, or retryable error.
- Map backend errors to field-level or form-level messages.
- Define partial failure behavior for batch or multi-step submissions.
- Map every field rule, async check, submit state, backend error, CSRF/idempotency control, and partial-failure path to validation evidence or residual risk.
- Add tests for invalid input, async validation, duplicate submit, and partial failure recovery.
- Name handoff boundaries and evidence limits so form-design output is not over-claimed as backend implementation, browser/a11y validation, legal copy approval, or production race proof.
