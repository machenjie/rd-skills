# Trajectory Privacy Fixture Boundary

Use this reference when trajectory evidence could retain sensitive runtime facts, produce behavior fixture candidates, or feed project memory. The `SKILL.md` body owns routing; this reference owns privacy classification, exclusion, retention, and promotion fields.

## Privacy Classes

| Class | Allowed fields | Excluded fields | Use |
| --- | --- | --- | --- |
| Public repo fact | Path family, file type, command class, validator name, pass/fail status. | Raw prompt, full command output, secrets, env values. | Normal repository trajectory review. |
| Bounded runtime fact | Stage, order, action class, owner/reviewer skill, result status, evidence limit. | User content, credentials, personal data, hidden chain-of-thought. | Runtime lifecycle review and compaction summaries. |
| Sensitive-excluded | Redacted path family, risk class, excluded-material note. | Tokens, keys, credentials, personal records, raw connector data. | Security/privacy handoff without retaining sensitive content. |
| Promotion-candidate | Structural failure pattern, excluded-sensitive list, proposed eval owner, rollback note. | Raw examples that identify users, secrets, or private conversations. | Human-reviewed fixture or benchmark proposal. |

## Retention Rules

1. Retain only bounded facts needed to prove order, freshness, review integrity, retry discipline, or closure limits.
2. Exclude raw prompts, secrets, personal data, environment variables, credentials, access tokens, full command arguments, and full command output.
3. Treat compaction summaries as selectors until final source, validation, and review evidence are rechecked.
4. Treat fixture candidates as private and structural until maintainer or eval-authoring review promotes them.
5. Do not write durable policy, registry rules, skill behavior, or benchmark fixtures directly from runtime trajectory evidence.

## Fixture Candidate Fields

```yaml
fixture_candidate:
  pattern: ""
  bounded_facts: []
  excluded_sensitive_material: []
  privacy_class: "promotion-candidate"
  proposed_eval_location: ""
  promotion_owner: ""
  validation_command: ""
  rollback_note: ""
  status: "candidate|deferred|approved|rejected"
```

## Promotion Gate

1. Name the professional behavior being tested, such as edit-before-read, stale validation, repair without re-review, repeated retry, or completion without residual risk.
2. Prove the candidate is bounded and reproducible without user-specific source material or raw prompts.
3. Route promotion to `skill-efficacy-benchmark` and `skill-authoring-expert`.
4. Track token and turn overhead as `not_collected` when unavailable; do not omit the field.
5. Keep the verdict conservative: candidate evidence is not measured live-agent improvement.
