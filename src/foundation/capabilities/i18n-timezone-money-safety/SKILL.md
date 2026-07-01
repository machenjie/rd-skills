---
name: i18n-timezone-money-safety
description: Designs internationalization, localization, timezone, date/time, currency, number formatting, collation, pluralization, locale fallback, and monetary precision safety.
license: MIT
changeforge_kind: foundation-capability
changeforge_capability_id: "100"
changeforge_version: 0.1.0
---

# Mission

Design internationalization, localization, date/time, timezone, currency, number formatting, sorting, pluralization, locale fallback, and monetary precision behavior so product logic remains correct across regions, languages, calendars, financial representations, runtime data upgrades, and client/server boundaries.

# Pinned Tooling Baseline

Pinned versions are review baselines, not permanent recommendations. If a pinned baseline is EOL, superseded, unsupported, or conflicts with the target project's approved platform policy, update this capability before relying on it for new product work. Use BCP 47 locale tags, CLDR/ICU locale data, IANA tzdata, runtime-native timezone libraries, decimal or minor-unit money representation, ISO 4217 currencies, ICU MessageFormat, Unicode normalization, and ICU collation. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed runtime baselines, field-classification matrices, DST/rounding decisions, graph/memory/trajectory evidence rules, and anti-pattern review.

# When To Use

Use this capability when a change touches localized UI text, translated messages, locale negotiation, date or time display, timezone conversion, scheduling, cutoff dates, recurring events, currency display, monetary calculation, tax or payment amounts, decimal precision, numeric formatting, collation, pluralization, search/sort order, language fallback, or API fields consumed across locales.

# Do Not Use When

Do not use this capability for copy edits with no locale, formatting, time, numeric, or money behavior. Do not use it instead of `api-contract-design` for contract fields, `sql-professional-usage` for database query semantics, or `payment-trading-extension` for regulated financial workflow rules.

# Stage Fit

Use during intake when locale, timezone, calendar, currency, number, sorting, pluralization, or formatting assumptions are hidden in a request. Use during design when API/storage/display boundaries, civil-time semantics, migration/backfill, locale fallback, or money precision must be decided before implementation. Use during coding, bug-fix, debugging, code-review, refactoring, testing, and release readiness when behavior depends on locale/time/money correctness. Use during review when repository graph, project memory, or previous execution suggests existing formatting helpers, tzdata baselines, money fields, translation keys, or currency rules that must be current-source confirmed. Hand off when the primary question is payment ledger policy, API contract rollout, SQL physical tuning, frontend display implementation, backend persistence, migration execution, or executable test strategy.

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

# Mode Matrix

| Mode | Trigger signals | Professional focus | Required evidence | Companion capabilities | Skip by default |
| --- | --- | --- | --- | --- | --- |
| Locale and text behavior | New translated text, locale negotiation, fallback, interpolation, plural/select, bidi, collation, or search/sort behavior. | Keep message keys, fallback, pluralization, normalization, and display boundaries locale-correct. | Supported locales, BCP 47 tags, CLDR/ICU version, message format, fallback and coverage evidence. | `frontend-change-builder`, `user-flow-modeling`, `quality-test-gate` | English-only string branching. |
| Timezone and civil-time modeling | Date, "today", local deadline, schedule, recurrence, cutoff, SLA, billing period, or timezone conversion changes. | Separate instant, date-only, local datetime, recurrence, duration, and display semantics. | Field classification, timezone source, storage/API format, DST gap/overlap policy, tzdata floor. | `data-model-design`, `api-contract-design`, `backend-change-builder` | Server-local time assumptions. |
| Money and numeric precision | Currency, amount, tax, invoice, quote, price, discount, FX, percentage, unit, decimal parsing, or rounding appears. | Preserve exact representation, currency exponent, rounding mode, and boundary-safe display/parsing. | Money representation, ISO 4217 currency field, precision/scale, rounding rule, provider/domain handoff. | `payment-trading-extension`, `dto-schema-design`, `sql-professional-usage` | Binary floating point for money. |
| Contract and migration compatibility | Existing API/storage fields, clients, reports, exports, historical timestamps, or persisted currency assumptions change. | Preserve old/new compatibility and plan migration/backfill before behavior shifts. | Old/new fields, consumer list, migration/backfill plan, compatibility class, validation report. | `version-compatibility`, `data-migration-design`, `contract-testing` | One-step semantic change. |
| Reuse and evidence validation | Repository graph, project memory, helper library, prior eval, or old execution says i18n/time/money handling exists. | Accept only source-confirmed current helpers, data baselines, tests, and runtime versions. | Inspected paths, accepted/rejected memory, graph freshness, validation command/output, evidence limits. | `repository-context-map`, `repository-graph-analysis`, `project-memory-governance` | Copying stale helper assumptions. |

# Industry Benchmarks

Anchor against Unicode CLDR/ICU, BCP 47 and RFC 4647 locale negotiation, RFC 3339 and ISO 8601 timestamp formats, IANA tzdata, ISO 4217 currency exponents, decimal arithmetic standards, ECMA-402 `Intl`, ICU MessageFormat, W3C i18n/bidi guidance, runtime-native date/time APIs, PostgreSQL `TIMESTAMPTZ`/`NUMERIC`, and payment-provider minor-unit practice. Keep this body focused on routing, evidence, output, and gates; load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) for detailed baselines, classification matrices, DST and rounding decision trees, graph/memory/trajectory coupling, and anti-pattern review.

# Selection Rules

Select this capability when correctness depends on locale, timezone, date/time, numeric, currency, collation, or pluralization semantics. Pair with `frontend-change-builder` for display behavior, `backend-change-builder` for business logic, `data-api-contract-changer` for API fields, `payment-trading-extension` for financial domain rules, `quality-test-gate` for boundary tests, and language professional usage capabilities for runtime-specific libraries.

# Proactive Professional Triggers

- **Signal:** request uses "today", "end of day", "monthly", "local time", "deadline", "recurring", "business day", or "timezone" without a timezone source. **Hidden risk:** server-local or UTC-only logic shifts customer-visible deadlines around DST and regions. **Required professional action:** classify each time field and define timezone source, storage/API shape, and DST gap/overlap policy. **Route to:** `data-model-design`, `api-contract-design`, `quality-test-gate`. **Evidence required:** field classification, tzdata baseline, DST boundary test, and source evidence.
- **Signal:** money, price, amount, tax, invoice, discount, FX, settlement, or percentage uses a bare number. **Hidden risk:** binary float, implicit currency, wrong exponent, or undocumented rounding causes reconciliation and customer disputes. **Required professional action:** pair amount with ISO 4217 currency, choose minor units or fixed decimal, and document rounding per operation. **Route to:** `payment-trading-extension`, `dto-schema-design`, `sql-professional-usage`. **Evidence required:** representation, currency source, rounding test, and payment-domain handoff or skip reason.
- **Signal:** localized text includes counts, gender, selection, user input, mixed scripts, or fallback. **Hidden risk:** English plural logic, unsafe interpolation, bidi spoofing, or silent missing translations ships to localized markets. **Required professional action:** require ICU MessageFormat, interpolation rules, bidi/normalization handling, and coverage metrics. **Route to:** `frontend-change-builder`, `input-validation`, `quality-test-gate`. **Evidence required:** locale matrix, pseudo-localization or coverage report, and normalization/collation test.
- **Signal:** API/storage fields carry localized display strings, locale-formatted dates, floats for money, or ambiguous date strings. **Hidden risk:** clients cannot parse deterministically and old consumers break across locale or version changes. **Required professional action:** separate canonical API/storage values from display formatting and classify compatibility. **Route to:** `api-contract-design`, `version-compatibility`, `contract-testing`. **Evidence required:** old/new field map, contract example, consumer impact, and validation result.
- **Signal:** repository graph, project memory, helper names, or previous execution says i18n/time/money handling already exists. **Hidden risk:** stale helper behavior, old tzdata/CLDR, changed currency assumptions, or untested locale paths are reused as truth. **Required professional action:** confirm current helpers, runtime versions, tests, and data contracts before reuse. **Route to:** `repository-context-map`, `repository-graph-analysis`, `project-memory-governance`, `execution-trajectory-analysis`. **Evidence required:** inspected paths, accepted/rejected evidence, validation freshness, and remaining unknowns.

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

- **Wrong cutoff date:** Symptom: invoice issued with wrong cutoff date for an Australia/Sydney customer.
  Cause: cutoff computed in server (UTC) local time.
  Detection: integration test with non-server timezone and DST transition day.
  Impact: revenue mis-recognition, customer dispute.
- **Cent drift:** Symptom: monetary total drifts by cents over many transactions.
  Cause: amounts stored as `float` / `double` / JS `Number`.
  Detection: linter forbids float types for money fields; reconciliation test sums 10 000 random amounts and asserts exact equality.
  Impact: ledger imbalance, audit finding.
- **Unparseable API date:** Symptom: mobile client fails to parse API date.
  Cause: API emits locale-formatted string instead of RFC 3339.
  Detection: contract test asserts ISO 8601 with `Z` or explicit offset.
  Impact: client crash, broken release.
- **UTC-only recurrence:** Symptom: recurring "Monday 09:00 NY" event fires at 08:00 NY for half the year.
  Cause: stored as UTC instant instead of `(local_time, IANA zone)`.
  Detection: DST-boundary test (March / November US transition).
  Impact: missed meetings, missed SLAs.
- **Silent translation fallback:** Symptom: untranslated English strings appear in zh-CN UI.
  Cause: fallback silently substituted source locale; no coverage metric.
  Detection: CI runs `i18n-coverage` per locale; warns < 95 %, fails < 85 %.
  Impact: brand / quality perception, missed launch criteria.
- **Non-normalized search:** Symptom: search by user name fails for `Müller` when stored as `Mueller`.
  Cause: byte-wise comparison; no NFC normalization; no locale-aware collation.
  Detection: collation unit test for de-DE phone-book order.
  Impact: broken search, duplicate accounts.
- **English plural ternary:** Symptom: Arabic UI shows "1 file(s)" or grammatical errors.
  Cause: English-only plural ternary; no ICU MessageFormat.
  Detection: pseudo-localization run in CI exercises plural and gender forms.
  Impact: user trust loss in localized markets.
- **Binary-float rounding:** Symptom: pricing rounds 1.005 to 1.00 instead of 1.01.
  Cause: IEEE 754 binary float (1.005 is actually 1.00499...) plus `HALF_UP`.
  Detection: decimal rounding test with documented mode.
  Impact: regulatory exposure, customer complaint.
- **Tzdata reinterpretation:** Symptom: chargeback after tzdata update changes a historical offset.
  Cause: stored civil time without zone, reinterpreted under new tzdata.
  Detection: data audit; pin tzdata at runtime and at processing job; convert at ingest and store both instant and (local_time, zone).
  Impact: financial discrepancy.

# Reference Loading Policy

The `SKILL.md` body carries L1/L2 i18n/time/money selection, stage fit, routing, evidence, output, and quality gates. Load [references/checklist.md](references/checklist.md) when drafting or reviewing a concrete locale, timezone, date/time, money, number, collation, translation, API/storage, migration, or test plan. Load [references/evidence-patterns.md](references/evidence-patterns.md) only when the handoff needs source-to-validation mapping, graph/memory/trajectory freshness, runtime baseline proof, tool permission boundary, or residual-risk wording. Load [references/benchmarks-and-patterns.md](references/benchmarks-and-patterns.md) when runtime/tooling baselines, field-classification matrices, DST gap/overlap policy, rounding/exponent rules, graph/memory/trajectory reuse, compatibility, or anti-pattern depth is needed. Use [examples/example-output.md](examples/example-output.md) only when the expected output shape is unclear. Do not load references for copy-only or pure routing work where this body is enough.

# Output Contract

Return an i18n/timezone/money safety design with:

- `mode_selected` (locale/text behavior, timezone/civil-time modeling, money/numeric precision, contract/migration compatibility, or reuse and evidence validation)
- `source_evidence` (brief, source files, API/schema, database fields, translation catalog, frontend display code, backend logic, reports, tests, repository graph, project memory, execution trajectory, and freshness limits)
- `graph_memory_trajectory_judgment` (accepted, rejected, stale, and unknown evidence for existing helpers, runtime baselines, data assumptions, and tests)
- `locale_model`: supported BCP 47 tags, negotiation order, fallback chain, missing-translation behavior, CLDR version
- `text_model`: message-key naming, interpolation rules, ICU MessageFormat usage, plural / gender / select coverage, pseudo-localization plan
- `time_model`: instant vs civil date vs civil datetime per field, timezone source per user / tenant, storage format (UTC + IANA zone), API format (RFC 3339), DST gap/overlap policy, tzdata version floor
- `money_model`: representation (minor-unit integer or fixed-point decimal), currency source field, precision and scale, rounding mode per operation, FX policy, minor-unit-aware display
- `number_model`: decimal separator, grouping, percent, units, parsing strictness, validation rules
- `collation_model`: sort/search locale, normalization (NFC), case/accent strength, special script handling
- `contract_impact`: API/storage field changes, backward compatibility plan, migration / backfill plan
- `tests`: locale matrix (≥ 3 incl. RTL), timezone matrix (≥ 3 incl. half-hour offset), DST boundaries, currency-precision (zero-exponent and three-exponent currencies), rounding modes, fallback, collation, parsing
- `i18n_time_money_to_validation_map`: each locale, message pattern, time field, money field, contract field, migration/backfill, runtime baseline, and fallback behavior mapped to validator/test/manual review or residual risk
- `handoff_boundaries`: owners for product rules, API contract, frontend display, backend persistence, data migration, payment review, security/privacy, reliability, and release work outside this capability
- `validation_evidence`: commands, reports, artifacts, outputs, and exit codes inspected, with what evidence proves and what it does not prove
- `evidence_limits`: uninspected locales, clients, runtime CLDR/tzdata, provider currency exponents, production data, historical timestamps, legal/compliance rules, and manual launch controls

# Evidence Contract

Close an i18n/timezone/money safety design only when these answers are concrete:

- **Basis:** selected mode, affected locale/time/money surfaces, product boundary, canonical-vs-display boundary, and benchmark/runtime baseline.
- **Current evidence:** source paths, API/schema fields, translation catalogs, database columns, display components, tests, reports, repository graph, project memory, and execution trajectory inspected with freshness limits.
- **Semantic proof:** every time value is classified, every money value has representation/currency/rounding, every localized message with variables uses locale-aware patterns, and every canonical contract rejects display-only formats.
- **Compatibility proof:** old clients, old persisted values, historical timestamps, existing translation keys, reports, exports, and generated clients are preserved or intentionally migrated.
- **Validation proof:** validation command, validator, test, report, artifact, output, and exit code are named when available; state what evidence proves, what evidence does not prove, residual risk, next gate, reuse and placement rationale, and behavior preservation.
- **Limits:** payment ledger correctness, legal deadline interpretation, production CLDR/tzdata rollout, live provider behavior, and complete locale linguistic review are not over-claimed.

# Benchmark Coverage

Improved i18n/time/money designs reject weak patterns: server-local "today", UTC-only recurrence, locale-formatted API dates, bare money amounts, binary floats, English plural ternaries, byte-order collation, display parsing as canonical input, silent translation fallback, stale tzdata/CLDR assumptions, and project-memory reuse without current-source confirmation. Detailed runtime baselines, DST/currency matrices, and anti-pattern review belong in references so this body stays efficient.

# Routing Coverage

Route here when correctness depends on locale, language, timezone, civil time, date/time display, monetary precision, currency, number parsing/formatting, collation, pluralization, or locale fallback. Hand off when primary ownership is payment ledger policy (`payment-trading-extension`), API rollout (`data-api-contract-changer` / `version-compatibility`), migration execution (`data-migration-design`), frontend implementation (`frontend-change-builder`), backend implementation (`backend-change-builder`), SQL physical behavior (`sql-professional-usage`), or executable validation strategy (`quality-test-gate`).

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
11. Selected mode, source evidence, and graph/memory/trajectory reuse judgment are explicit.
12. Every locale, message pattern, time field, money field, rounding rule, contract field, migration/backfill, fallback, and runtime baseline maps to validation evidence or named residual risk.
13. Handoff boundaries and evidence limits are explicit so design evidence is not over-claimed as payment compliance, production data migration, legal deadline interpretation, or complete linguistic review.

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
