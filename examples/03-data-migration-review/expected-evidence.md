# Expected Evidence

- inspect: migration files, model definitions, API serializers, background jobs, analytics queries, rollback policy, and deployment order.
- validation evidence: inspect available migration and rollback test results, schema diff, and mixed-version compatibility fixtures; report which old/new readers and writers they cover. Missing executable proof is a gap, not a passing result, and the reviewer does not repair or execute the migration.
- independent review: the assigned release reviewer assesses whether same-release removal breaks reachable consumers or rollback and reports concrete findings with source evidence.
- required action: when a reachable old reader remains, describe the compatible rollout change and its required tests. Any later authorized implementation belongs to a Task; ordinary repair followed by fresh targeted validation does not automatically require another Review.
- residual risk: downstream reporting queries or deployment behavior not represented by the available source and evidence.
- result: reviewed files, compatibility findings, rollout and rollback assessment,
  validation limits, unverified scope, residual risk, and any owner decision
  needed before implementation. No change or production action is implied.
