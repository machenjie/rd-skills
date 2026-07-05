# Example Output

```markdown
## Scope Boundary

Mode selected:
- V1 scope boundary with anti-scope-creep review.

Source evidence:
- Ticket `EXP-1842` requests monthly export eligibility filtering only.
- Current CSV contract test `export_schema_v1` preserves column order.
- Repository graph shows export scheduling lives in a separate module and was not inspected beyond route ownership.
- Project memory about a future reporting redesign is not accepted as current scope because no approved roadmap item is linked.

In scope:
- Exclude closed accounts from standard monthly export.
- Preserve existing CSV column names and order.
- Preserve audit-mode export behavior.

Out of scope:
- Redesign account lifecycle states. Forbidden artifacts: new lifecycle enum values, lifecycle migration, lifecycle admin UI.
- Add export scheduling. Forbidden artifacts: scheduler route, cron job, queue topic, schedule UI.
- Add reporting redesign fields. Forbidden artifacts: nullable future CSV columns or placeholder API fields.

Version boundary:
- This release changes eligibility filtering only.
- v1 CSV schema and field order remain immutable for existing consumers.
- Later reporting redesign must not be assumed by current schema, API, or export job contract.

Forbidden assumptions:
- Do not assume all closed accounts are safe to hide from audit workflows.
- Do not add speculative columns for future reporting.
- Do not create an export scheduling flag or empty scheduling endpoint.

Future compatibility judgment:
- V1 does not block a later reporting redesign because it preserves the existing contract and only changes standard-export filtering.
- Scheduling can be added later without current placeholder jobs.

Acceptance exclusions:
- Verify `POST /exports/schedules` is not defined.
- Verify CSV output does not include new future reporting columns.
- Verify no migration adds account lifecycle states.

Anti-scope-creep checks:
- Diff review confirms no account lifecycle model changes.
- Contract test confirms CSV schema is unchanged.
- Route search confirms no scheduling endpoint.
- Job registry search confirms no scheduling worker.

Changed scope to validation map:
- Closed-account standard export filter -> integration test `standard_export_excludes_closed_accounts`.
- Audit-mode preservation -> regression test `audit_export_includes_closed_accounts`.
- CSV compatibility -> contract test `export_schema_v1`.
- Scheduling non-goal -> route and job registry review; residual risk if generated OpenAPI is not rebuilt.

Handoff boundaries:
- `acceptance-standard-definition` owns final falsifiable criteria.
- `quality-test-gate` owns test-layer selection and freshness.
- `data-api-contract-changer` owns any future CSV/API version change.

Evidence limits:
- Production data volume was not inspected.
- Future reporting roadmap was not validated with product authority.
- Generated OpenAPI output must be checked after final route changes if routes are edited later.
```
