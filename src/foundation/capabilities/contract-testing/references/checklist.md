# Contract Testing Checklist

- Name provider, consumer classes, contract surface, source, versions, release order, and replay or retention sources.
- Mark unknown consumers and undocumented or observed behavior before choosing a compatibility claim.
- Cover semantic branches used by consumers: absent/null/default, errors, authorization, unknown values, ordering, pagination, duplicates, and replay where triggered.
- Exercise relevant old/new producer-consumer combinations and generated-client/runtime versions.
- Pair provider verification with consumer-side parsing, compilation, or behavior for named consumers.
- Scope registry, broker, diff, and fixture results to their subject, selector, environment, capture, and compatibility policy.
- Redact credentials and tenant data in captured payloads; record provenance and drift triggers.
- Re-run affected proof after contract, fixture, generator, policy, or consumer-selection changes.
- Record unavailable consumers, environments, retained payloads, and rollout evidence as explicit non-proof boundaries.
