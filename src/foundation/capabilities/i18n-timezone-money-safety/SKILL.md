---
name: i18n-timezone-money-safety
description: Designs internationalization, localization, timezone, date/time, currency, number formatting, collation, pluralization, locale fallback, and monetary precision safety.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "100"
changeforge_version: 0.1.0
---

# Mission

Design internationalization, localization, date/time, timezone, currency, number formatting, sorting, pluralization, locale fallback, and monetary precision behavior so product logic remains correct across regions, languages, calendars, and financial representations.

# Pinned Tooling Baseline

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work.

- Locale tags: IETF BCP 47 (RFC 5646); validate with `Intl.Locale` (ECMA-402) or `Locale.forLanguageTag` (Java); reject non-canonical tags.
- Locale data: Unicode CLDR ≥ 44; pin the CLDR version used by the build; ICU ≥ 73 for server-side formatting.
- Time zones: IANA Time Zone Database (tzdata) ≥ 2024a; pin the tzdata version in the container image; subscribe to tzdata announcement list.
- Runtime libraries: Python `zoneinfo` (stdlib 3.9+) preferred over `pytz`; Node `Intl.*` + `Temporal` polyfill (proposal-temporal) or `date-fns-tz` ≥ 3 / `luxon` ≥ 3; Java `java.time` (JSR-310) only — never `java.util.Date` for new code; Go `time` with explicit `time.LoadLocation`; .NET `TimeZoneInfo` + `NodaTime` ≥ 3 for civil-time semantics.
- Money types: Python `decimal.Decimal` (set context via `decimal.localcontext`); Java `BigDecimal` with explicit `RoundingMode` and `MathContext`; JavaScript `decimal.js` ≥ 10 or `dinero.js` ≥ 2 (immutable, currency-aware); Go `shopspring/decimal` ≥ 1.3; SQL `NUMERIC(p, s)` (never `FLOAT`/`REAL`/`DOUBLE`).
- Currency codes: ISO 4217 alpha-3; respect minor-unit exponents from ISO 4217 (e.g., JPY = 0, USD = 2, BHD = 3, CLF = 4).
- Translation pipeline: ICU MessageFormat 2 (recommended) or MessageFormat 1 with full plural / select; tooling such as `gettext` (xgettext / msgmerge), `Format.JS`, `i18next`, `LinguiJS`, `Crowdin` / `Phrase` / `Lokalise` for translation memory.
- Normalization: Unicode NFC at API boundary (RFC 8264 PRECIS for identifiers); collation via ICU `Collator` (`Intl.Collator`).

# When To Use

Use this capability when a change touches localized UI text, translated messages, locale negotiation, date or time display, timezone conversion, scheduling, cutoff dates, recurring events, currency display, monetary calculation, tax or payment amounts, decimal precision, numeric formatting, collation, pluralization, search/sort order, language fallback, or API fields consumed across locales.

# Do Not Use When

Do not use this capability for copy edits with no locale, formatting, time, numeric, or money behavior. Do not use it instead of `api-contract-design` for contract fields, `sql-professional-usage` for database query semantics, or `payment-trading-extension` for regulated financial workflow rules.

# Non-Negotiable Rules

- Store instants in UTC (RFC 3339 with `Z` suffix or epoch nanos) and store the user's intended IANA timezone separately when civil-time semantics matter.
- Never use binary floating-point (`float`, `double`, `Number`) for money or any precise decimal; use minor-unit integers or fixed-precision decimal types with an explicit currency.
- Every monetary value crosses module / API / storage boundaries paired with its ISO 4217 currency code; bare numeric amounts are forbidden unless the enclosing contract pins a single currency in its schema.
- Keep canonical storage and API formats distinct from display formats; display formatting happens at the presentation edge.
- Define locale negotiation order (`Accept-Language` → user setting → tenant default → product default), fallback chain (`zh-Hant-HK` → `zh-Hant` → `zh` → `en`), and missing-translation behavior (fail-loud in dev, source-locale in prod with a metric).
- Use CLDR/ICU pluralization (`one`, `two`, `few`, `many`, `other`, plus locale-specific rules); never hard-code English singular/plural ternary.
- Define DST policy explicitly for scheduling: nonexistent local times (spring-forward gap) must reject or shift forward; ambiguous local times (fall-back overlap) must choose earlier or later and record the choice.
- Round monetary amounts with a documented rounding mode (`HALF_EVEN` / banker's rounding is the default for accounting; `HALF_UP` only when a regulation requires it).
- Apply Unicode NFC normalization at the API input boundary; never compare unnormalized strings.
- Sort and search localized text via ICU collation (`Intl.Collator`), not byte order; specify strength (primary / secondary / tertiary).
- Pin and ship CLDR and tzdata versions explicitly; refuse to deploy if the runtime tzdata is older than the documented floor.

# Industry Benchmarks

- Unicode CLDR ≥ 44 and Unicode 15.1 standard.
- IETF BCP 47 (RFC 5646) language tags; RFC 4647 lookup.
- ISO 8601:2019 and RFC 3339 timestamp formats.
- IANA Time Zone Database (tzdata) — current series.
- ISO 4217 currency codes and minor-unit exponents.
- IEEE 754-2008 decimal arithmetic and ANSI X3.274 / `decimal` context semantics; never IEEE 754 binary for money.
- ICU MessageFormat 2 (Unicode Technical Standard #35 Part 9, 2024).
- ECMA-402 Intl API (current edition).
- W3C Internationalization Best Practices (`<html lang>`, `dir`, `lang` per element).
- Java JSR-310 `java.time`; Python PEP 615 `zoneinfo`; PostgreSQL `TIMESTAMPTZ` and `NUMERIC`.
- Payment-provider minor-unit handling (Stripe, Adyen, Braintree all use minor units).

# Selection Rules

Select this capability when correctness depends on locale, timezone, date/time, numeric, currency, collation, or pluralization semantics. Pair with `frontend-change-builder` for display behavior, `backend-change-builder` for business logic, `data-api-contract-changer` for API fields, `payment-trading-extension` for financial domain rules, `quality-test-gate` for boundary tests, and language professional usage capabilities for runtime-specific libraries.

# Risk Escalation Rules

- Escalate to `payment-trading-extension` for payments, billing, ledgers, tax, FX, trading, settlement deadlines, or persisted monetary values.
- Escalate to `delivery-release-gate` when migration / backfill of historic timestamps or currencies is required.
- Escalate to legal / compliance for jurisdiction-bound deadlines (tax cutoffs, GDPR / DSAR clocks, statute-of-limitations windows).
- Escalate to `security-privacy-gate` when locale data may be used for tracking (canvas fingerprinting via `Intl`).
- Escalate to critical when existing production data has ambiguous timezone (`timestamp without time zone`) or implicit currency assumptions; backfill must precede behavioral change.

# Critical Details

- Date-only values (birthdays, service days, billing periods, local deadlines) are civil dates, not instants; store as `DATE` / `LocalDate` and never convert through a timezone.
- A user-visible "today" depends on user timezone, not server timezone; query boundaries (`WHERE created_at >= today_start`) must compute the boundary in the user's tz then convert to UTC.
- DST gaps and overlaps: spring-forward creates nonexistent local times (e.g., 02:30 local on the change day); fall-back creates two instants for one local time. Java `ZonedDateTime` policies: `ofStrict`, `ofLocal`-with-`ZoneRules`; Python `zoneinfo` raises `NonExistentTimeError` / `AmbiguousTimeError` via `fold` attribute.
- Recurring events ("every Monday at 09:00 New York time") must store the IANA zone, not the UTC offset; offsets shift across DST.
- Currencies: ISO 4217 exponent dictates minor units (USD = 100 cents, JPY = 1, BHD = 1000 fils, CLF / UYW = 10 000). Cash rounding rules (e.g., Swiss 0.05) are separate from accounting rounding.
- Rounding mode is a business rule: `HALF_EVEN` (banker's, default for IEEE 754 decimal and most accounting), `HALF_UP` (regulatory in some jurisdictions), `DOWN` (truncation, used by some tax authorities). Document per money operation.
- Sorting: byte order misorders accented Latin and ideographic scripts; use ICU `Collator` with locale and strength. German phone-book vs dictionary order differ; Thai sort uses cluster grouping; Chinese sort varies by stroke vs pinyin.
- Pluralization: Arabic has 6 plural forms, Russian has 4, Polish has 3, Welsh has 5; the English `if (n === 1) singular else plural` template is wrong everywhere else.
- APIs carry canonical values (`amount_minor`, `currency`, `timestamp_utc`, `timezone`); clients render via `Intl.NumberFormat` / `Intl.DateTimeFormat`.
- Bidi (RTL) text needs `dir="auto"` or explicit `dir`; never assume LTR layout in mixed-script strings; Unicode bidi-control characters (U+202A-U+202E, U+2066-U+2069) require sanitization in user input (Trojan Source CVE-2021-42574).
- Locale data drift: a tzdata or CLDR upgrade can change formatting and offsets; golden tests must pin and assert.

# Failure Modes

- Symptom: invoice issued with wrong cutoff date for an Australia/Sydney customer.
  Cause: cutoff computed in server (UTC) local time.
  Detection: integration test with non-server timezone and DST transition day.
  Impact: revenue mis-recognition, customer dispute.
- Symptom: monetary total drifts by cents over many transactions.
  Cause: amounts stored as `float` / `double` / JS `Number`.
  Detection: linter forbids float types for money fields; reconciliation test sums 10 000 random amounts and asserts exact equality.
  Impact: ledger imbalance, audit finding.
- Symptom: mobile client fails to parse API date.
  Cause: API emits locale-formatted string instead of RFC 3339.
  Detection: contract test asserts ISO 8601 with `Z` or explicit offset.
  Impact: client crash, broken release.
- Symptom: recurring "Monday 09:00 NY" event fires at 08:00 NY for half the year.
  Cause: stored as UTC instant instead of `(local_time, IANA zone)`.
  Detection: DST-boundary test (March / November US transition).
  Impact: missed meetings, missed SLAs.
- Symptom: untranslated English strings appear in zh-CN UI.
  Cause: fallback silently substituted source locale; no coverage metric.
  Detection: CI runs `i18n-coverage` per locale; warns < 95 %, fails < 85 %.
  Impact: brand / quality perception, missed launch criteria.
- Symptom: search by user name fails for `Müller` when stored as `Mueller`.
  Cause: byte-wise comparison; no NFC normalization; no locale-aware collation.
  Detection: collation unit test for de-DE phone-book order.
  Impact: broken search, duplicate accounts.
- Symptom: Arabic UI shows "1 file(s)" or grammatical errors.
  Cause: English-only plural ternary; no ICU MessageFormat.
  Detection: pseudo-localization run in CI exercises plural and gender forms.
  Impact: user trust loss in localized markets.
- Symptom: pricing rounds 1.005 to 1.00 instead of 1.01.
  Cause: IEEE 754 binary float (1.005 is actually 1.00499...) plus `HALF_UP`.
  Detection: decimal rounding test with documented mode.
  Impact: regulatory exposure, customer complaint.
- Symptom: chargeback after tzdata update changes a historical offset.
  Cause: stored civil time without zone, reinterpreted under new tzdata.
  Detection: data audit; pin tzdata at runtime and at processing job; convert at ingest and store both instant and (local_time, zone).
  Impact: financial discrepancy.

# Output Contract

Return an i18n/timezone/money safety design with:

- `locale_model`: supported BCP 47 tags, negotiation order, fallback chain, missing-translation behavior, CLDR version
- `text_model`: message-key naming, interpolation rules, ICU MessageFormat usage, plural / gender / select coverage, pseudo-localization plan
- `time_model`: instant vs civil date vs civil datetime per field, timezone source per user / tenant, storage format (UTC + IANA zone), API format (RFC 3339), DST gap/overlap policy, tzdata version floor
- `money_model`: representation (minor-unit integer or fixed-point decimal), currency source field, precision and scale, rounding mode per operation, FX policy, minor-unit-aware display
- `number_model`: decimal separator, grouping, percent, units, parsing strictness, validation rules
- `collation_model`: sort/search locale, normalization (NFC), case/accent strength, special script handling
- `contract_impact`: API/storage field changes, backward compatibility plan, migration / backfill plan
- `tests`: locale matrix (≥ 3 incl. RTL), timezone matrix (≥ 3 incl. half-hour offset), DST boundaries, currency-precision (zero-exponent and three-exponent currencies), rounding modes, fallback, collation, parsing
- `handoff`: owners for product rules, API contract, frontend display, backend persistence, data migration, and payment review

# Quality Gate

1. No money field uses a binary floating-point type; CI lint enforces.
2. Every money field is paired with an ISO 4217 currency in the same struct/row.
3. Every persisted timestamp is `TIMESTAMPTZ` / UTC instant; civil-time scenarios additionally store the IANA zone.
4. API responses use RFC 3339 timestamps and minor-unit money; contract tests assert.
5. The test matrix covers at least 3 locales (incl. one RTL and one with complex pluralization), 3 timezones (incl. one with a half-hour offset and one with DST), and the spring-forward and fall-back boundary days.
6. Rounding mode is documented per money operation and asserted by a test using both `1.005`-class and zero-exponent (`JPY`) inputs.
7. Translation coverage is measured per locale in CI; missing-translation behavior is defined and observable.
8. ICU MessageFormat (or equivalent) is used for any user-visible string with a number, date, or selection; English ternary plurals are banned.
9. Sorting and search use `Intl.Collator` (or ICU `Collator`) at the documented strength; byte-wise comparison is banned for user-visible names.
10. CLDR and tzdata versions are pinned in the build manifest; deployment refuses runtimes below the floor.

# Used By

- frontend-change-builder
- backend-change-builder
- data-api-contract-changer
- payment-trading-extension
- quality-test-gate
- typescript-professional-usage
- python-professional-usage
- java-jvm-professional-usage
- sql-professional-usage

# Handoff

Hand off to `data-api-contract-changer` for canonical API fields, `payment-trading-extension` for money movement and ledger rules, `quality-test-gate` for boundary coverage, `frontend-change-builder` for localized display, `backend-change-builder` for business logic, and the matching language or SQL professional usage capability for runtime-specific date/time and decimal handling.

# Completion Criteria

The capability is complete when locale, timezone, date/time, currency, numeric, collation, pluralization, fallback, storage, API, display, migration, and test expectations are explicit enough to prevent region-specific correctness defects under DST transitions, tzdata updates, multi-currency rounding, and RTL / complex-plural locales.
