# Example Output

```markdown
## I18n Timezone Money Design

mode_selected: timezone/civil-time modeling with money/numeric precision

source_evidence:
- Inspected: appointment API schema, scheduling service, invoice amount model, translation catalog, locale display tests.
- Not inspected: production tzdata image version, live payment provider minor-unit table, and historical timestamp backfill sample.

graph_memory_trajectory_judgment:
- Accepted: repository graph links appointment API to scheduling service and display component.
- Rejected: old project memory saying all customers use `America/New_York`; current tenant settings include multiple IANA zones.
- Unknown: last production CLDR/tzdata rollout date.

locale_model:
- Supported locales: en-US, fr-FR, ja-JP.
- Fallback: requested locale -> language -> en-US; missing translations fail in CI and emit a production metric.

text_model:
- ICU MessageFormat is required for count-bearing strings.
- Pseudo-localization covers appointment and invoice flows before release.

time_model:
- Appointment starts are stored as UTC instants plus original IANA timezone.
- User-facing "today" is evaluated in the user's timezone.
- Nonexistent DST times are rejected with a validation error.
- Ambiguous DST overlap chooses the earlier instant and records the policy.

money_model:
- Amounts use minor-unit integers plus ISO 4217 currency.
- Rounding mode: half-up for invoice display; ledger stores exact minor units.

contract_impact:
- API returns `starts_at_utc`, `timezone`, `amount_minor`, and `currency`; clients never receive locale-formatted canonical fields.
- Existing locale-formatted export remains supported for one release while new canonical export fields are added.

i18n_time_money_to_validation_map:
- fr-FR number formatting: component test.
- ja-JP currency display and JPY zero-decimal amount: unit + contract examples.
- America/New_York DST skip and Europe/Paris DST repeat: scheduling integration tests.
- API canonical fields: OpenAPI example validation.

handoff_boundaries:
- data-api-contract-changer owns canonical API field rollout.
- quality-test-gate owns the locale/timezone/currency matrix.
- payment-trading-extension is required before changing ledger or settlement rules.

evidence_limits:
- This design does not prove production tzdata, payment provider behavior, legal deadline interpretation, or full linguistic review.
```
