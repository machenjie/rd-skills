# Consumer and Data Impact

Use this Reference only when public or indirect consumers or authoritative data ownership may change.

## Decision Rules

- Only when public or indirect consumers or authoritative data ownership can change, state known/unknown consumers. Also state the contract or data-owner delta, any compatibility/versioning or migration need, rollout boundary, and evidence for preserved behavior.
- When public or indirect consumers may be affected, require bounded discovery and compatibility evidence with an additive change, adapter, version, migration, deprecation, or coordinated cutover selected from current contracts.
- When authoritative data ownership can move or split, require one source-of-truth decision, transition behavior, consistency boundary, and recovery evidence scoped to the actual ownership impact.
- Public or indirect boundaries require consumer and compatibility/versioning proof when that boundary changes.
- Record the affected consumers, data authority, rollout boundary, compatibility decision, and validation evidence.
