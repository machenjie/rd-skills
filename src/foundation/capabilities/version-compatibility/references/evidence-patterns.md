# Version Compatibility Evidence Patterns

Use this reference when compatibility closure depends on old/new matrix proof, generated-client freshness, schema registry evidence, telemetry gate proof, rollback evidence, stale consumer memory, or proof limits. Keep it as an evidence map, not another compatibility benchmark catalog.

## Compatibility Surface-To-Validation Map

| Compatibility claim | Minimum evidence | What it proves | What it does not prove |
| --- | --- | --- | --- |
| API/DTO change is compatible | Old/new schema diff, structure/meaning/default/error review, consumer list, and contract fixture | Inspected request/response surface matches declared compatibility class | Unknown consumers, generated clients, or partner behavior are covered |
| Event/schema change is compatible | Schema registry mode, old/new producer-consumer matrix, replay fixture, retention window, and consumer inventory | Inspected event payload can be read in declared directions | Lagged consumers, DLQ behavior, or unregistered schemas are fully safe |
| Stored data/config rollback is safe | Old/new reader-writer matrix, config bridge/precedence, migration phase, rollback query, and release order | Inspected old/new binaries can coexist under named assumptions | Production data distribution, every deployment skew, or emergency rollback is proven |
| SDK/package/export compatibility is current | Public API diff, generated-client diff, semver decision, downstream compile/test, and changelog note | Inspected package surface matches declared version class | Unpublished consumers or all language-specific runtime behavior is compatible |
| Deprecation removal is gated | Usage telemetry, threshold, elapsed window, notification/owner approval, and removal validation | Inspected deprecated surface met named removal criteria | Future calls, uninstrumented clients, or all partner schedules are exhausted |
| Prior consumer evidence is fresh | Current source/generated/telemetry paths, accepted/rejected memory, validator/report, and final-edit freshness | Reused compatibility claim still matches inspected source | Later schema, client, config, topic, or deployment edits remain covered |

## Evidence Quality Labels

- **Strong evidence**: current contracts, generated artifacts, consumers, telemetry, migration/config paths, and tests inspected; command/report and freshness recorded; proof limits named.
- **Weak evidence**: local caller search only, docs-only deprecation, schema-only diff, happy-path 200 fixture, old generated-client report, or prior claim without current source.
- **Missing evidence**: no old/new matrix, no rollback state, no consumer inventory, no generated-client check, no telemetry gate, no schema registry mode, or no owner for unknown consumers.
- **Invalid evidence**: breaking change shipped as patch/minor, old code cannot read new data on rollback, enum expansion lacks unknown handling for strict consumers, or stale "no consumers" memory accepted as proof.

- If production telemetry query, schema registry mutation, deployment flag change, partner notification, migration, or rollback rehearsal, require owner, scope, dry-run or staging proof, stop condition, rollback/forward-fix path, and redaction.
