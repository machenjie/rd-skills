# Example Output

```markdown
## AI Coding Context Package

Goal:
- Add idempotent retry handling to invoice webhook processing.

Relevant files:
- src/webhooks/invoice_handler.py
- src/billing/repository.py
- tests/integration/test_invoice_webhook.py

Contracts:
- Provider retries with same event id.
- Handler must return success for duplicate processed events.

Constraints:
- Do not change invoice state machine transitions.
- Do not log webhook payload secrets.

Quality gates:
- Unit tests for duplicate event decisions.
- Integration test for provider retry path.

Refresh if:
- Webhook contract or invoice state model changes.
```
