# Example Output

```markdown
## DTO Schema Contract

DTO: RefundRequest
Direction: Client request.

Fields:
- amount: required decimal string; must be greater than 0.
- reason: required enum CUSTOMER_REQUESTED, FRAUD, DUPLICATE.
- note: optional nullable string; null clears note, missing leaves note absent.
- idempotency_key: required string; max 128 characters.

Mapping:
- amount maps to Money value object.
- reason maps to RefundReason domain enum.
- note is not stored when missing.

Compatibility:
- New optional fields may be added.
- Renaming reason values requires a new API version or compatibility bridge.
```
