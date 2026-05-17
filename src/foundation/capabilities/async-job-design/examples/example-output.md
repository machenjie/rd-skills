# Example Output

```markdown
## Async Job Design

Job:
- Generate monthly invoice PDF.

Trigger:
- Enqueued after invoice is finalized.

Payload:
- invoiceId, tenantId, requestedBy, correlationId.
- No invoice totals snapshot; worker reloads finalized invoice by id.

Idempotency:
- Output key is invoiceId plus document type.
- Duplicate job returns existing generated document.

Retry and timeout:
- Timeout after 5 minutes.
- Retry transient renderer or storage failures 3 times with backoff.
- Do not retry missing finalized invoice; mark failed_permanent.

Status:
- pending, running, succeeded, failed_retryable, failed_permanent, cancelled.

Compensation:
- If storage succeeds but metadata update fails, cleanup orphaned object or reconcile by output key.
```
