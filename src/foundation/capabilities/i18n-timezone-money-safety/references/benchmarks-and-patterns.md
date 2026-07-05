# I18n Timezone Money Safety Benchmarks And Patterns

Use this reference when `i18n-timezone-money-safety` needs more depth than the main `SKILL.md` should carry efficiently. Keep the main body focused on selection, evidence, output, and gates; use this file for runtime baselines, semantic classification matrices, DST and rounding decisions, graph/memory/trajectory coupling, validation design, and anti-pattern review.

## Contents

- [Runtime And Data Baselines](#runtime-and-data-baselines)
- [Benchmark Anchors](#benchmark-anchors)
- [Locale And Text Matrix](#locale-and-text-matrix)
- [Time Field Classification Matrix](#time-field-classification-matrix)
- [DST And Recurrence Decision Tree](#dst-and-recurrence-decision-tree)
- [Money And Number Matrix](#money-and-number-matrix)
- [API, Storage, And Display Boundary](#api-storage-and-display-boundary)
- [Graph, Memory, And Execution Coupling](#graph-memory-and-execution-coupling)
- [Validation Matrix](#validation-matrix)
- [Review Checklist](#review-checklist)
- [Anti-Patterns To Reject](#anti-patterns-to-reject)
- [Handoff Boundaries](#handoff-boundaries)

## Runtime And Data Baselines

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update the capability before relying on it for new product work.

- Locale tags: IETF BCP 47 (RFC 5646); validate with `Intl.Locale` or platform equivalent; reject non-canonical tags.
- Locale lookup: RFC 4647 lookup or clearly documented product fallback chain.
- Locale data: Unicode CLDR and ICU versions pinned by build/runtime image; record version in validation evidence.
- Time zones: IANA Time Zone Database pinned in images and jobs; tzdata upgrades require regression review for affected regions.
- Runtime libraries: prefer runtime-native civil-time APIs (`java.time`, Python `zoneinfo`, Go `time.LoadLocation`, .NET `NodaTime` where civil semantics matter, Node `Intl` plus `Temporal` or approved library).
- Money types: use minor-unit integers or fixed-precision decimal (`Decimal`, `BigDecimal`, decimal libraries, SQL `NUMERIC(p, s)`); never binary float for money.
- Currency codes: ISO 4217 alpha-3 with minor-unit exponents; cash rounding rules are separate product/domain rules.
- Translation pipeline: ICU MessageFormat 2 or MessageFormat 1 with plural/select support; translation memory and coverage tooling must be owned.
- Normalization and collation: Unicode NFC at API boundary; ICU/CLDR collation for user-visible sort/search.

## Benchmark Anchors

- Unicode CLDR/ICU for locale, plural, collation, calendar, number, and currency formatting.
- BCP 47 and RFC 4647 for language tags and fallback lookup.
- ISO 8601 and RFC 3339 for canonical timestamp interchange.
- IANA tzdata for named time zones and historical/political offset changes.
- ISO 4217 for currency codes and minor-unit exponents.
- Decimal arithmetic standards and language decimal contexts for precise money math.
- ECMA-402 `Intl` for browser and JavaScript runtime formatting.
- W3C Internationalization guidance for `lang`, `dir`, bidi isolation, and mixed-script UI.
- Runtime-native date/time APIs such as Java JSR-310 and Python PEP 615.
- PostgreSQL `TIMESTAMPTZ`, `DATE`, and `NUMERIC` semantics for storage boundary review.

## Locale And Text Matrix

| Surface | Required decision | Evidence |
| --- | --- | --- |
| Supported locales | Exact BCP 47 tags, launch scope, tenant/user availability. | Product locale list and canonical tag validation. |
| Negotiation | User setting, tenant default, `Accept-Language`, product default order. | Negotiation test and fallback examples. |
| Missing translations | Fail-loud in dev/CI, source-locale fallback or blocked release in prod. | Coverage report and missing-key metric. |
| Interpolation | Named placeholders, escaping rules, translator notes. | Message catalog lint. |
| Plural/select | ICU categories per locale; no English ternary branch. | Locale matrix with complex plural locale. |
| Bidi and mixed script | `dir`, bidi isolation, control-character handling. | RTL UI or string-rendering test. |
| Collation/search | Locale, strength, normalization, accent/case behavior. | Sort/search fixture with accented and non-Latin names. |

## Time Field Classification Matrix

| Field type | Store as | API shape | Examples | Common trap |
| --- | --- | --- | --- | --- |
| Instant | UTC timestamp with offset or epoch precision. | RFC 3339 UTC/offset. | Event created time, payment captured time. | Formatting instant as local date before storage. |
| Civil date | Date without timezone. | `YYYY-MM-DD`. | Birthday, service day, billing date. | Converting through UTC and shifting date. |
| Civil datetime | Local date/time plus IANA zone. | `local_datetime` + `timezone`. | Appointment at local branch. | Storing only UTC and losing user intent. |
| Recurrence | Rule plus local time plus IANA zone. | RRULE-like rule, local time, zone. | Every Monday at 09:00. | Storing fixed UTC offset. |
| Duration | Numeric duration with unit. | ISO 8601 duration or explicit unit. | Trial length, timeout. | Adding duration to local time without DST policy. |
| Reporting period | Named period with timezone/calendar. | Period start/end canonicalized. | Month-to-date revenue. | Using server timezone for tenant reports. |

## DST And Recurrence Decision Tree

```text
Does the value represent a historical event that already happened?
  YES -> store UTC instant; display in viewer or event timezone.

Does the value represent a local date or civil deadline?
  YES -> store DATE or local date; do not convert through UTC.

Does the value represent a future local time chosen by a user or tenant?
  YES -> store local date/time plus IANA timezone and define:
    - nonexistent local time policy: reject or shift forward;
    - ambiguous local time policy: earlier or later instant;
    - tzdata upgrade behavior for future scheduled events.

Does it recur at local wall-clock time?
  YES -> store recurrence rule, local time, and IANA timezone; never store only UTC offset.
```

## Money And Number Matrix

| Surface | Required decision | Evidence |
| --- | --- | --- |
| Representation | Minor-unit integer or fixed decimal; scale and precision. | Type/schema review and lint forbidding binary float. |
| Currency | ISO 4217 field in same object/row or contract-pinned single currency. | Schema/DTO example and validation. |
| Exponent | Currency minor-unit exponent and display behavior. | Tests for zero-, two-, and three-exponent currencies. |
| Rounding | Operation-specific rounding mode and timing. | Tests with `1.005`-class values and JPY/BHD. |
| Parsing | Whether localized input is accepted; strict grammar; canonical conversion. | Parser tests for decimal separators and invalid grouping. |
| FX | Rate source, timestamp, rounding, and audit. | Payment/trading handoff unless clearly out of scope. |
| Tax/cash rounding | Jurisdiction and cash rounding separate from accounting rounding. | Legal/payment owner or residual risk. |

## API, Storage, And Display Boundary

| Boundary | Canonical form | Display form |
| --- | --- | --- |
| API timestamp | RFC 3339 UTC/offset plus timezone when intent matters. | `Intl.DateTimeFormat` or platform formatter at client/display edge. |
| API money | `amount_minor` + `currency`, or decimal string + currency when justified. | Locale-aware currency display. |
| Storage instant | `TIMESTAMPTZ`/UTC instant. | Not stored as display string. |
| Storage civil date | `DATE`/LocalDate. | Locale-specific rendered date. |
| Translation key | Stable key plus ICU message. | Rendered text after locale selection. |
| Search/sort | Normalized value plus locale-aware collation strategy. | User-visible sorted list. |

Never parse localized display strings as canonical API input unless the contract explicitly defines locale, parser strictness, and failure behavior.

## Graph, Memory, And Execution Coupling

| Evidence input | Accept when | Reject or downgrade when |
| --- | --- | --- |
| Repository graph | Current translation catalogs, format helpers, date/time utilities, money types, schemas, migrations, tests, reports, and generated clients were inspected. | Graph proximity is treated as proof that semantics or validation exist. |
| Project memory | Prior locale/time/money decision has owner, date, unchanged source paths, and matching runtime baseline. | Memory predates currency, tenant, timezone, provider, CLDR, tzdata, API, or report changes. |
| Execution trajectory | Validation ran after the latest material edit and covers locale/time/money boundaries. | Output is stale, happy-path-only, or from another runtime/provider. |
| Runtime baseline | CLDR/tzdata/currency table versions are read from build/runtime evidence. | Version is inferred from library names or local machine only. |
| Provider behavior | Payment, tax, FX, or calendar provider rules are documented and current. | Provider assumptions are copied from examples or old docs without source. |

Strong outputs state what was accepted, rejected, stale, unknown, and what each validation command proves or does not prove.

## Validation Matrix

| Risk | Minimum validation |
| --- | --- |
| Locale negotiation | User setting, tenant default, `Accept-Language`, and product default order tests. |
| Translation coverage | Per-locale coverage report and missing-key failure/metric. |
| Complex pluralization | Arabic/Russian/Polish or target-market equivalent plural tests. |
| RTL/bidi | RTL rendering or string isolation test with mixed-script data. |
| DST gap/overlap | Spring-forward nonexistent time and fall-back ambiguous time tests. |
| Half-hour/odd offset | Timezone such as Asia/Kolkata, Australia/Adelaide, or Pacific/Chatham. |
| Date-only | Date remains stable across UTC conversions and user timezone shifts. |
| Money precision | Zero-, two-, and three-exponent currency cases plus `1.005` rounding. |
| API canonical shape | Contract examples reject locale-formatted dates/money as canonical fields. |
| Migration/backfill | Representative historical timestamp/currency sample and rollback/residual limit. |
| Collation/search | Accent/case/script sort fixture for target locales. |

## Review Checklist

- Supported locales and canonical BCP 47 tags are explicit.
- Negotiation and fallback order are deterministic.
- Missing translation behavior is observable and release-gated when needed.
- Text with counts, dates, gender, or choices uses ICU MessageFormat or equivalent.
- Every time field is classified as instant, date, local datetime, recurrence, duration, or reporting period.
- Timezone source and DST gap/overlap policy are explicit.
- API/storage canonical values are separate from display values.
- Money representation, currency, exponent, rounding, parsing, and display are explicit.
- CLDR, ICU, tzdata, and currency data baselines are pinned or marked not verified.
- Repository graph, project memory, and execution trajectory are current-source confirmed or marked stale/unknown.
- Compatibility, migration, backfill, generated-client, report/export, and provider impacts are named.
- Every material field or behavior maps to validation evidence or residual risk.

## Anti-Patterns To Reject

| Anti-pattern | Failure | Safer treatment |
| --- | --- | --- |
| Server-local "today". | Region-specific deadlines shift. | Compute in user/tenant timezone, convert boundary to UTC for queries. |
| UTC-only recurring event. | Local wall-clock time changes across DST. | Store recurrence rule, local time, and IANA zone. |
| Locale-formatted API timestamp. | Clients parse differently or fail. | RFC 3339 canonical timestamp plus display at edge. |
| Bare `amount: 10.5`. | Currency/exponent and decimal precision are ambiguous. | `amount_minor` + `currency`, or decimal string + currency with scale. |
| Binary float for money. | Cent drift and reconciliation failure. | Minor units or decimal type with explicit rounding. |
| English plural ternary. | Complex plural locales render wrong grammar. | ICU plural/select message. |
| Byte-wise sort. | Names sort/search incorrectly in target locales. | ICU collation with locale and strength. |
| Silent fallback to English. | Localized launch quality is unknown. | Coverage threshold and missing-key metric. |
| Old memory says timezone is fixed. | Tenant/user expansion creates wrong behavior. | Confirm current tenant/user timezone source. |

## Handoff Boundaries

- Use `data-api-contract-changer` or `api-contract-design` for canonical API field rollout and contract examples.
- Use `version-compatibility` for old/new clients, generated clients, exports, and deprecation windows.
- Use `data-model-design` and `data-migration-design` for persisted field semantics, historical backfill, and rollback.
- Use `frontend-change-builder` for display widgets, locale negotiation UI, RTL layout, and client formatter placement.
- Use `backend-change-builder` for business rules, query boundaries, and persistence edge formatting.
- Use `payment-trading-extension` for ledger, settlement, tax, FX, payment provider, or regulated money workflow policy.
- Use `security-privacy-gate` when locale/timezone data can fingerprint users or when bidi/control characters affect trust boundaries.
- Use `quality-test-gate` for the executable locale/timezone/currency/collation validation matrix.
