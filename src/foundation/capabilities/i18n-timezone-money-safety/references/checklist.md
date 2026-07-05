# I18n Timezone Money Safety Checklist

- Select the mode before writing the design.
- State source evidence, accepted/rejected repository graph evidence, project memory, execution trajectory, and freshness limits.
- Define supported locales, BCP 47 tags, negotiation, fallback, and missing translation behavior.
- Separate canonical API/storage formats from localized display formats.
- Classify each time value as instant, local date, local datetime, recurring local time, or duration.
- Define timezone source, DST policy, ambiguous time behavior, and server-time assumptions.
- Represent money as minor-unit integer or fixed-precision decimal with ISO 4217 currency.
- Define precision, rounding mode, currency exponent, tax/payment constraints, and display format.
- Define pluralization, interpolation, collation, normalization, and localized search/sort behavior.
- Identify API, database, migration, generated-client, report/export, and backward compatibility impact.
- Map old/new clients, persisted values, historical timestamps, translation keys, reports, and exports to preservation or migration behavior.
- Add tests across locales, timezones, DST boundaries, currencies, rounding cases, fallback, collation, parsing, and canonical/display boundaries.
- Map each locale, message pattern, time field, money field, contract field, migration/backfill, runtime baseline, and fallback behavior to validation evidence or residual risk.
- Name handoff boundaries for API, frontend, backend, data migration, payment, security/privacy, reliability, release, and legal/compliance review.
- State evidence limits and uninspected production/runtime/provider/legal behavior.
