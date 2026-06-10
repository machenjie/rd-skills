Selected stage: code-review.
Selected professional skill: integration-change-builder.
Selected capabilities: web-security, idempotency-retry-design, message-queue-design, input-validation.

Hidden risks: forged webhook event mutates subscription state; replayed event duplicates side effects; parsed body invalidates HMAC verification.

Inspected boundaries: raw request body, signature header, constant-time HMAC compare, event ID dedupe store, replay window, subscription mutation path, invalid schema handling.

Evidence required: raw-body signature verification and constant-time compare; event ID dedupe store and replay window; duplicate-event and invalid-signature tests.

Validation command: `python3 -m pytest tests/integration/test_webhook_security.py` (not run in fixture; expected outcome is signature-failure and replay test output).
What evidence proves: invalid signatures are rejected before mutation and duplicate event IDs do not reapply side effects.
What evidence does not prove: provider outage ordering across delayed retries.

Output obligations covered: inbound webhook security analysis; validation evidence for signature failure and replay; residual provider delivery risk.

Residual risk: provider delivery ordering remains outside local control; owner: integration-change-builder.
Next gate: security-privacy-gate if subscription state is regulated or billing-sensitive.
