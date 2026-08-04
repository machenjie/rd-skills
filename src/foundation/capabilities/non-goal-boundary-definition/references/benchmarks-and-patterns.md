# Non-Goal Boundary Definition Benchmarks And Patterns

Load this reference when scope exclusions, deferred behavior, version boundaries, or speculative artifacts could change implementation. Do not load it to exclude correctness, security, privacy, compliance, data integrity, compatibility, reliability, or other behavior required for the accepted goal.

## Valid Exclusion Contract

| Field | Required content |
| --- | --- |
| Included behavior | Actor, surface/data/version, observable outcome, and acceptance owner. |
| Excluded behavior | Concrete action/outcome not delivered now; distinguish deferred, rejected, future-version, and separately owned work. |
| Forbidden artifacts | Name the endpoint, schema, field, flag, UI, job, event, dependency, adapter, documentation, configuration, or other scaffold whose accidental introduction is credible in the selected task slice and whose absence the final check can inspect. |
| Check | Diff/source/contract/generated/build/test query proving the forbidden artifact is absent after the final edit. |
| Revisit | Accountable owner, trigger/expiry, dependency, and evidence needed before the exclusion changes. |

An exclusion is valid only when the accepted behavior remains correct and safe without it. Required authorization, validation, rollback/recovery, audit, migration compatibility, deletion/privacy, or operational protection cannot be relabeled “out of scope” merely to reduce work.

Version boundaries name current and future actors, clients, and data plus old and new behavior. They also name allowed or forbidden compatibility bridges, generated artifacts, migration or backfill, rollout, and the removal owner. Deferring “v2 later” does not authorize nullable columns, reserved enums, disabled endpoints, placeholder flags/events, empty adapters, or coming-soon UI now.

## Failure And Proof Limits

Reject schedule-only non-goals, “security/performance/rollback later” when required for current correctness, speculative shared scaffolding, hidden TODOs, and deferred work with no owner/trigger. A not-present check proves only the inspected current diff/build; it cannot guarantee future work stays excluded. Repository topology does not prove scope authority, and a roadmap note is not an accepted requirement.

Record conflict resolution when a non-goal contradicts acceptance, policy, data/contract compatibility, or an invariant; escalate to the owner rather than silently choosing the narrower scope.

Route blocking scope authority to `requirement-clarification` and traceable brief updates to `requirement-structuring`. Route pass/fail exclusion checks to `acceptance-standard-definition` and `quality-test-gate`. Route consumer/version boundaries to `version-compatibility`, data/release exclusions to their Professional owners, and accepted sequencing to `task-dag-planner`.
