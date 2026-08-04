# I18n Timezone Money Evidence Patterns

- Source boundary: translation catalogs, locale negotiation code, formatter helpers, API/schema fields, database columns, reports/exports, generated clients, tests, runtime image, and owner.
- Locale/text evidence: supported BCP 47 tags, CLDR/ICU version, fallback chain, missing-key behavior, ICU MessageFormat usage, bidi handling, normalization, and collation fixture.
- Time evidence: field classification, timezone source, storage/API shape, DST gap/overlap policy, recurrence rule, tzdata floor, and old/new client impact.
- Money identity evidence: exact representation, ISO or non-ISO currency or asset identity, and namespace.
- Parser syntax evidence: governing input contract, accepted numeric syntax, and canonical/display boundary.
- Locale parser evidence: contract-specific decimal and grouping separators plus whitespace, sign, and exponent-notation policies.
- Coercion and rejection evidence: contract-permitted coercions plus rejection behavior for unsupported or ambiguous separators, malformed grouping, non-finite values, excess precision, and trailing data.
- Scale evidence: authoritative scale or exponent source and freshness, precision, operation-specific rounding and timing, overflow, and invalid-value handling.
- Boundary evidence: provider/domain handoff plus zero-, high-scale, mismatch, rounding-boundary, overflow, and accepted/rejected parser fixtures for separators, whitespace, and exponent notation.
- Compatibility evidence: historical timestamps, persisted currency assumptions, generated clients, reports/exports, migration/backfill sample, rollback or residual owner.
- current source/diff/validation evidence: inspected paths, accepted/rejected helper claims, stale prior task evidence, latest validation time, and what remains unknown.

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
- current source/diff/validation freshness:
- Tool permission boundary:
- Validation:
- What remains unproved:
- Residual risk:
```

## Blocking Conditions

- Block completion when canonical and display formats are mixed.
- Block money completion when identity, scale or exponent authority, precision, rounding, overflow, or validation proof is missing.
- Block civil-time completion when timezone or DST policy is missing.
- Block compatibility completion when historical data is unmapped.
- Block stale prior evidence and artifact-writing validation that omits write scope or rollback disclosure.
