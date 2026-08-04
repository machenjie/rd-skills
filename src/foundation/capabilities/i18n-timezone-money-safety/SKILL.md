---
name: i18n-timezone-money-safety
description: "`analysis-agent`/`task-agent`/`review-agent`: use when locale, timezone, date/time, currency, formatting, plurals, fallback, or rounding changes; skip unaffected semantics."
---

# i18n-timezone-money-safety

## Registry Trigger

**Use when**

- internationalization localization timezone date time currency number formatting collation pluralization locale fallback monetary precision rounding

**Do not use when**

- no task-local i18n timezone money safety decision is required

## Skill Role

Define locale authority, translation fallback, temporal semantics, timezone conversion, monetary representation, rounding, collation, and formatting boundaries. Exclude pricing, payment authorization, and storage migration.

## High-Value Rules

- **Separate canonical value from presentation.** Preserve language-neutral identifiers, instants, civil dates, quantities, currency, and numeric values through domain and storage boundaries; localize only at the owned presentation or parsing boundary.
- **Name locale and timezone authority.** Resolve user preference, tenant or business context, device or request hints, and fallback precedence explicitly; do not infer business timezone or language from machine defaults.
- **Model temporal kind before conversion.** Distinguish instant, local civil time, date-only, duration, recurrence, and calendar period, then define daylight-saving gaps, overlaps, offset changes, and clock uncertainty for the affected operation.
- **Carry currency and rounding semantics with money.** Preserve currency identity, precision or scale, calculation rounding stage, allocation behavior, display rounding, and reconciliation source from the current business contract.
- **Treat parsing, formatting, sorting, and searching as distinct contracts.** Define accepted localized input, canonical storage, display output, collation, normalization, and equality so presentation changes cannot alter identity silently.
- **Make fallback and missing content observable.** Distinguish untranslated, intentionally inherited, unsupported, and invalid resources; prevent fallback from hiding policy, legal, safety, or transactional wording gaps.
- **Test representative boundary cases from supported data.** Cover current locale families, scripts, plural categories, calendars, timezone transitions, currency precision, negative values, and mixed-version resource behavior relevant to the task.

## Anti-Patterns

- Store formatted dates, localized numbers, or display strings as canonical business values.
- Apply one global locale, timezone, currency precision, or rounding rule across contexts with different authorities.
- Treat translated string equality, machine timezone, floating-point display, or a happy-path snapshot as semantic proof.

## Stop Conditions

Escalate when locale or timezone authority is ambiguous, temporal kind is unknown, money lacks currency or rounding ownership, or fallback can change legal or transactional meaning. Also escalate when persisted formatted data needs migration or supported locale and timezone data cannot exercise the affected boundary.

## Output Contract

- internationalization safety decision with canonical values, locale and timezone authority, temporal kind, money and rounding semantics, fallback behavior, representative boundary evidence, and proof limits

## Targeted References

| Path | Type | Load when | Do not load when | Required by | Required output |
|---|---|---|---|---|---|
| [benchmarks and patterns](references/benchmarks-and-patterns.md) | benchmark-pattern | Locale, DST, currency, rounding, or canonicalization choices remain open | No locale, time, or monetary semantics change | task-agent, analysis-agent, review-agent | option-comparison, selected-approach |
| [checklist](references/checklist.md) | decision-checklist | Change spans fallback, ambiguous time, precision, or display boundaries | Values have no locale, time, or money meaning | task-agent, analysis-agent, review-agent | checklist-result, residual-risk |
| [evidence patterns](references/evidence-patterns.md) | evidence-pattern | Safety claims need current CLDR, tzdata, schema, or migration proof | No localization, temporal, or monetary claim needs validation | task-agent, analysis-agent, review-agent | evidence-record, proof-limit, residual-risk |
