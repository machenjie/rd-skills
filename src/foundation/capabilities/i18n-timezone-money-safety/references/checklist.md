# I18n Timezone Money Safety Checklist

- Define supported locales, BCP 47 tags, negotiation, fallback, and missing translation behavior.
- Separate canonical API/storage formats from localized display formats.
- Classify each time value as instant, local date, local datetime, recurring local time, or duration.
- Define timezone source, DST policy, ambiguous time behavior, and server-time assumptions.
- Represent money as minor-unit integer or fixed-precision decimal with ISO 4217 currency.
- Define precision, rounding mode, currency exponent, tax/payment constraints, and display format.
- Define pluralization, interpolation, collation, normalization, and localized search/sort behavior.
- Identify API, database, migration, and backward compatibility impact.
- Add tests across locales, timezones, DST boundaries, currencies, rounding cases, fallback, and collation.
