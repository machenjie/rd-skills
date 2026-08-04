# Failure Contract Design Evidence Patterns

Use this reference when failure-contract closure depends on validation freshness, prior source or task evidence, safe representation, cause preservation, or proof limits. Keep it as an evidence map, not a second error-code, retry, queue, or observability catalog.

## Failure-Claim-To-Validation Map

| Failure claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| Failure taxonomy is machine-distinguishable | State table, local type/code/result, owner boundary, and negative assertion | Changed states can be distinguished in inspected paths | Every external provider failure shape is covered |
| Raw failure is translated at owning boundary | Raw source failure, translation code, public mapping, diagnostic mapping, and cause preservation | Dependency details are not knowingly leaked across inspected boundary | Unknown generated clients or downstream wrappers are safe |
| Retryable and terminal meaning is correct | Classified states, timeout/cancellation/unknown stance, caller decision, specialist route, and negative evidence | Inspected callers receive distinct retry meaning | Retry identity, timing, deduplication, or queue behavior is proven |
| Partial or degraded meaning has ownership | Completed and incomplete effects, reduced-quality meaning, external representation, residual owner, and specialist route | Escaped or degraded outcomes are not hidden | Routed compensation, fallback, or reconciliation will succeed |
| External and internal representations are safe | User/consumer-safe meaning, preserved authorized cause, boundary context, and no-raw-detail proof | Inspected representations avoid obvious leakage without discarding cause | Every sink, retention policy, or support export is approved |
| Validation is fresh after final failure edit | Command/review/report path, changed failure states, exit code or manual result, final edit scope, and freshness | Evidence covers the final inspected failure contract | Untested chaos, live provider, or production-only failures are proven |

## Current Evidence And Freshness

- Treat repository inspection, generated specs or clients, prior task evidence, incident notes, validation output, and logs as selectors until current source, tests, generated artifacts, and owner evidence confirm them.
- Accept prior "error handling is safe", "provider errors are mapped", "retryability is known", or "no raw leak" only when current callers, adapters, generated clients, tests, and validation still match.
- Mark evidence stale after edits to translation code, external representations, fallback meaning, failure classification, partial/degraded results, generated specs, tests, or validation outputs.
- Map each changed taxonomy, translation, retry classification, partial or degraded meaning, safe representation, and residual risk to fresh evidence or explicit not-run disclosure, with mechanism proof assigned to its specialist owner.
