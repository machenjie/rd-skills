# Example Output

```markdown
## Event Catalog

Event: ExportCompleted
Meaning: A monthly export finished and a downloadable file is available.
Producer: Export worker after file metadata commit.
Payload:
- export_id
- tenant_id
- reporting_period
- file_id
- completed_at
- schema_version

Consumers:
- Notification service sends analyst notification.
- Audit service records export completion.
- Reporting projection updates export list.

Delivery rules:
- Idempotency key: export_id + event_name + schema_version.
- Ordering: Ordered per export_id only.
- Retry: Exponential backoff; dead-letter after configured exhaustion.
- Duplicate handling: Consumers ignore already processed idempotency key.

Audit impact:
- Event is audit-significant and must preserve actor and export identifiers.
```
