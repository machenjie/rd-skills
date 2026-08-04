# I18n Timezone Money Safety Benchmarks And Patterns

Load this reference when locale/text, civil-time/DST, canonical/display boundaries, currency, rounding, collation, or related migration semantics change. Do not load it for untranslated internal identifiers or numeric values with no locale/time/money meaning.

## Locale And Text

| Concern | Required decision and proof |
| --- | --- |
| Locale support/negotiation | Canonical supported tags, user/tenant/request/default precedence, fallback, and unavailable-locale behavior with current product evidence. |
| Messages | Stable keys, named escaped interpolation, plural/select rules for supported locales, translator context, and missing-key visibility/release policy. |
| Direction and mixed script | Document language/direction, bidi isolation/control handling, logical layout, and applicable RTL/mixed-script tests. |
| Normalization/collation/search | Define normalization and locale/strength/case/accent policy per field. When exact bytes or code points carry identifier, credential, signature, or protocol meaning, preserve them unless the owning contract explicitly defines equivalence; verify changed round-trip or signature/interoperability behavior. |

Runtime CLDR/ICU/tzdata/currency/message-format versions come from the built/deployed environment and are recorded when behavior depends on them. Named libraries and pinned versions are candidates, not universal answers.

## Time Semantics

| Meaning | Canonical model | Easy-to-miss failure |
| --- | --- | --- |
| Instant that occurred | UTC/offset timestamp with declared precision. | Storing a formatted local string or losing precision/offset semantics. |
| Civil date | Date without timezone. | Converting through UTC and shifting the intended day. |
| Future local datetime | Local date/time plus IANA zone and DST resolution policy. | Storing only UTC or a fixed offset and losing future user intent. |
| Recurrence | Rule + local time + IANA zone + gap/overlap/tzdata-change policy. | Reusing one UTC instant/offset across DST. |
| Duration/deadline/reporting period | Explicit unit/clock/calendar/timezone and boundary inclusivity. | Server-local “today,” wall-clock duration math, or ambiguous month/day boundaries. |

For nonexistent local times, choose rejection or shift behavior from the product contract.
For ambiguous local times, choose earlier or later behavior from that contract.
Do not hide either choice in a library default.
Test target-market DST gaps and overlaps, relevant odd offsets, date-only stability, and deployed tzdata compatibility.

## Money And Numeric Semantics

Authoritative money uses a decimal or minor-unit representation with currency, scale/exponent, precision, operation-specific rounding mode and timing, and overflow behavior. Binary float is not proof-safe for authoritative amounts. Localized parsing is accepted only with a declared locale grammar and rejection behavior; APIs/storage keep canonical values separate from display strings.

FX, tax, cash rounding, settlement, ledger, and provider values name rate/rule source, timestamp/effective period, jurisdiction, audit/reconciliation, and domain owner. ISO currency metadata is a baseline, not a substitute for current product/provider/legal rules.

## Evidence And Proof Limits

Inspect current catalogs, format/parsing helpers, schemas/DTOs, storage/migrations, reports/exports, generated clients, runtime images, and provider rules. Sample locales do not cover the supported-language set. Local tzdata does not prove deployment. Formatter tests do not prove legal, tax, or payment correctness. Visual RTL does not prove bidi safety. Sample conversions do not prove historical backfill.

Reject server-local dates, UTC-only recurrences, localized canonical timestamps or amounts, and bare amounts without currency semantics. Also reject binary float for authoritative money, English-only plural branches, byte-wise user-visible sorting, silent unowned fallback, and time-zone assumptions copied from stale evidence.

Route API rollout to data-api-contract-changer or api-contract-design, and old/new clients to version-compatibility. Route persistence/backfill to data-model-design and data-migration-design, and UI formatting/RTL to frontend-change-builder. Route business query rules to backend-change-builder, financial policy to payment-trading-extension, and trust risks to security-privacy-gate. Route executable locale/time/money proof to quality-test-gate.
