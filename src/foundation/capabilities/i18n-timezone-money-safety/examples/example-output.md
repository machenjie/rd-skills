# Example Output

```markdown
## I18n Timezone Money Design

Locale model:
- Supported locales: en-US, fr-FR, ja-JP.
- Fallback: requested locale -> language -> en-US.

Time model:
- Appointment starts are stored as UTC instants plus original IANA timezone.
- User-facing "today" is evaluated in the user's timezone.
- Nonexistent DST times are rejected with a validation error.

Money model:
- Amounts use minor-unit integers plus ISO 4217 currency.
- Rounding mode: half-up for invoice display; ledger stores exact minor units.

Tests:
- fr-FR number formatting, ja-JP currency display, America/New_York DST skip, Europe/Paris DST repeat, and JPY zero-decimal amount.
```
