# I18n Timezone Money Evidence Patterns

## Required Evidence

- Source boundary: translation catalogs, locale negotiation code, formatter helpers, API/schema fields, database columns, reports/exports, generated clients, tests, runtime image, and owner.
- Locale/text evidence: supported BCP 47 tags, CLDR/ICU version, fallback chain, missing-key behavior, ICU MessageFormat usage, bidi handling, normalization, and collation fixture.
- Time evidence: field classification, timezone source, storage/API shape, DST gap/overlap policy, recurrence rule, tzdata floor, and old/new client impact.
- Money/number evidence: representation, currency field, ISO 4217 exponent, rounding mode per operation, parser strictness, provider/domain handoff, and zero-/three-exponent tests.
- Compatibility evidence: historical timestamps, persisted currency assumptions, generated clients, reports/exports, migration/backfill sample, rollback or residual owner.
- Graph/memory/trajectory evidence: inspected paths, accepted/rejected helper claims, stale project memory, latest validation time, and what remains unknown.

## Tool Permission Boundary

Classify commands as read-only inspection, locale catalog generation, test/report write, migration/backfill dry run, runtime image/build write, provider/network lookup, or release publish. State sandbox/approval state, write scope (`HOME`, source tree, generated catalogs, report artifacts, `dist/`, CI workspace), rollback path, and secret/PII redaction rule.

## Handoff Shape

```markdown
I18n Time Money Evidence Record
- Source boundary:
- Locale/text proof:
- Timezone/civil-time proof:
- Money/number proof:
- Compatibility proof:
- Graph/memory/trajectory freshness:
- Tool permission boundary:
- Validation:
- What remains unproved:
- Residual risk:
```

## Blocking Conditions

Block completion when canonical and display formats are mixed, money lacks currency/rounding proof, civil time lacks timezone/DST policy, old clients or historical data are not mapped, project memory is reused without current-source confirmation, or artifact-writing validation lacks write-scope and rollback disclosure.
