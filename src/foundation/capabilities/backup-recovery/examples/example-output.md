# Example Output

```markdown
## Backup Recovery Plan

Change: Re-key customer document storage.

Protected data:
- document metadata table
- object storage files
- encryption key mapping

Targets:
- RPO: 15 minutes.
- RTO: 2 hours for affected tenant restore.

Validation:
- Restore latest backup into staging.
- Verify document count, checksum sample, and application read path.
- Confirm old and new key mappings can decrypt sampled files.

Owner:
- Storage operations lead owns restore drill before production rollout.
```
