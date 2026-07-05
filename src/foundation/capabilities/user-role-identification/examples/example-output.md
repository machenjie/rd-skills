# Example Output

```markdown
## Role Inventory

mode_selected: permission-sensitive discovery

role_inventory_scope:
- Surface: monthly account export from the finance workspace.
- Protected resources: account records, closed-account history, export files, tenant storage objects.
- Tenant boundary: finance users may export only assigned tenant data.
- Excluded actors: public visitors and unauthenticated users do not participate.

source_evidence:
- Inspected: export route, export worker job, finance role policy, storage writer docs, accounting platform contract.
- Not inspected: production IAM bindings and live accounting-platform credentials.

graph_memory_trajectory_judgment:
- Accepted: repository graph links export route to worker and storage writer.
- Rejected: old project memory saying support can download exports; current policy docs show metadata-only support access.
- Unknown: last production credential rotation date.

actor_taxonomy:
| Actor | Type | Trust | Auth | Tenant scope | Goal |
| --- | --- | --- | --- | --- | --- |
| Finance analyst | Role-differentiated human user | Medium | SSO session + role claim | Assigned tenant only | Run monthly export |
| Support agent | Privileged support role | High | SSO + MFA | Metadata for assigned support case | Diagnose failed export |
| Export worker | Service account | High machine | Workload identity | Job-scoped tenant | Generate file asynchronously |
| Accounting platform | External system | External limited | mTLS client identity | Contracted file only | Import CSV |

data_visibility_matrix:
| Actor | Visible | Hidden | Denied actions |
| --- | --- | --- | --- |
| Finance analyst | Eligible account fields for assigned tenant | Other tenants, raw payment data, support notes | Cross-tenant export, schema override |
| Support agent | Export metadata, status, request ID | Export file contents, account details | Download file, edit tenant scope |
| Export worker | Eligible source rows for job tenant | Unscoped tenant scans | Write outside export bucket prefix |
| Accounting platform | Final CSV columns | Internal IDs, support metadata | Query source API directly |

service_account_governance:
- export-worker: owner Finance Platform team; workload identity; read eligible account rows; write tenant-scoped export object; quarterly scope review; audit every job run.

external_actor_trust_contract:
- accounting-platform: mTLS required; accepts only stable CSV contract; cannot assert tenant or account eligibility; duplicate import handling handed to integration design.

support_admin_operator_model:
- Support is read-only for export metadata unless an elevated incident procedure is approved.
- No support or admin role may bypass tenant eligibility checks.

role_to_permission_boundary_map:
- Finance analyst export request: subject Finance analyst, resource account/export, action create export, condition assigned tenant.
- Export worker read/write: subject service account, resource account rows/export object, action read/write, condition job tenant and bucket prefix.
- Support metadata read: subject Support agent, resource export metadata, action read, condition ticket-bound case.

role_to_scenario_validation_map:
- Finance analyst: valid assigned-tenant export, denied cross-tenant export, empty eligible account set.
- Support agent: diagnose failed export without file download.
- Export worker: retry same job without duplicate object write.
- Accounting platform: rejected malformed CSV and duplicate import handling.

downstream_models_required:
- permission-boundary-modeling for analyst, support, and worker enforcement predicates.
- scenario-decomposition for valid, denied, retry, malformed file, and operational diagnosis paths.
- integration-change-builder for accounting-platform contract and duplicate import behavior.

handoff_boundaries:
- This inventory does not prove backend enforcement, credential rotation, contract tests, or production IAM state.

evidence_limits:
- Live production credentials and accounting-platform behavior were not verified.
```
