# Example Output

```markdown
## State Machine

Object: MonthlyExport

States:
- draft
- queued
- running
- failed
- completed
- canceled

Transitions:
| From | To | Trigger | Guard | Side Effect |
| --- | --- | --- | --- | --- |
| draft | queued | Analyst submits | User can create export | Create job record |
| queued | running | Worker starts | Job lease acquired | Record started_at |
| running | completed | Worker writes file | File checksum stored | Emit ExportCompleted |
| running | failed | Worker exhausts retry | Failure reason captured | Emit ExportFailed |
| queued | canceled | Analyst cancels | Job has not started | Emit ExportCanceled |

Illegal:
- completed -> running is rejected.
- failed -> completed is rejected without explicit retry transition.
```
