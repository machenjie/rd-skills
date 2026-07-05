# Business Rule Evidence Patterns

Use this reference when business-rule closure depends on rule-to-validation mapping, entry-point proof, owner review, audit traceability, or historical replay.

## Evidence Map
- **Rule authority:** prove stable rule id, owner, authoritative enforcement layer, source path, defense layers, and duplicate decision sites accepted or rejected.
- **Entry-point coverage:** prove UI, API, job, import, admin, replay, migration, support, or script paths call or reference the same authority.
- **Exception or override:** prove override rule id, allowed actor, evidence requirement, audit fields, expiry, precedence, and denied/allowed tests.
- **Historical or regulated rule:** prove effective dating, decision snapshot or version lookup, audit field, owner approval, replay case, and retention obligation.
- **Rule change readiness:** prove rule-to-validation map, owner review, implementation location, release blocker, stale command status, and residual risk owner.

## Evidence Rules
- Every accepted rule claim names source or owner evidence, validator/test/report artifact, freshness, what it proves, what it does not prove, and next gate.
- Project memory, repository graph, old tickets, support notes, spreadsheets, and generated summaries are discovery inputs only until current source, owner review, or validation confirms the rule.
