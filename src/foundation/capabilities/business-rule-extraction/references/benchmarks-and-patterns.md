# Business Rule Extraction Benchmarks And Patterns

Use this reference when root `SKILL.md` needs deeper support for rule authority, decision-table design, graph/memory/execution coupling, audit traceability, or changed-rule-to-validation mapping. Keep examples generic and do not include real customer data, secret values, private policy text, or regulated identifiers.

## Rule Evidence Matrix

| Rule Surface | Inspect | Evidence | Common False Proof |
| --- | --- | --- | --- |
| Domain model or policy object | Aggregate methods, policy/specification classes, domain services, rule ids. | Rule owner, allowed/denied unit cases, reason-code output, entry-point call path. | A service method happens to enforce the rule for one route. |
| SQL/stored procedure/report | `WHERE`, joins, computed columns, procedures, materialized views, reports. | Cataloged rule id, query owner, domain enforcement source, reconciliation test. | Treating the query as the only source of truth for a business decision. |
| UI/API/admin/import/job | Route handlers, UI hints, admin overrides, import scripts, queue consumers, migrations. | Entry-point inventory and proof each path calls or references the authoritative rule. | Happy-path API test while jobs or admin tools bypass the rule. |
| Spreadsheet/support macro/external artifact | Finance, risk, support, legal, or operations artifacts that define decisions. | Provenance, owner confirmation, effective date, migration or synchronization plan. | Copying spreadsheet values into code without owner or freshness. |
| Audit/history/replay | Decision snapshots, rule version table, event-time facts, audit log schema. | Replay test, audit fields, historical version lookup, owner acceptance. | Recomputing historical decisions with today's rules. |

## Rule Authority Decision Matrix

| Question | Professional Decision | Evidence Required |
| --- | --- | --- |
| Is this domain policy or input shape? | Route shape parsing to input validation; keep business meaning in the rule catalog. | Rejected transport-only fields and accepted domain facts. |
| Is this authorization? | Route who-may-act decisions to authorization capability while preserving business reason codes. | PEP/PDP boundary, denied tests, object/tenant scope. |
| Is this structural invariant? | Enforce in domain and defend with DB constraint when needed. | Aggregate owner, DB constraint, violation test, migration/backfill note. |
| Is this analyst-managed tabular policy? | Prefer decision table with hit policy and owner review. | DMN/table owner, precedence, effective dates, generated/tested artifact. |
| Is this high-change policy needing an engine? | Use OPA/Cedar/rules engine only with governance, versioning, and performance evidence. | Engine owner, bundle versioning, decision logs, latency/cache validation. |

## Graph, Memory, And Execution Coupling

- Repository graph selects duplicate decision sites, entry points, SQL/report paths, jobs/imports/admin scripts, test fixtures, generated artifacts, docs, support macros, and audit schemas.
- Project memory can identify prior disputed rules, spreadsheet authority, fragile bypass paths, or known support escalations; accept it only after current source, owner, or validation evidence confirms it.
- Execution trajectory decides whether rule validation, replay, owner review, or graph scan ran after the final rule/catalog/source edit.
- Validation broker maps each rule id to allowed/denied cases, entry-point checks, replay/audit checks, owner approval, release blocker, stale command, or residual risk.
- Agent-tool permission/sandbox evidence is required before running broad graph scans, data-replay scripts, spreadsheet exports, support-tool reads, migrations, or rule-engine bundle generation.

## Rule Validation Map

| Claim | Evidence Pattern | What It Proves | What It Does Not Prove |
| --- | --- | --- | --- |
| One authoritative owner | Owner record plus current source path for enforcement. | The inspected rule has one named authority. | Future team changes or uninspected support artifacts. |
| Entry points obey the rule | UI/API/job/import/admin/script inventory plus tests or review for each path. | Selected paths reference the same rule source. | Unknown runtime-only entry points or external tools. |
| Historical decision is reproducible | Snapshot or versioned rule lookup with replay case. | The tested event-time facts resolve to the documented decision. | All historical data quality or every old rule version. |
| Exceptions are controlled | Override rule id, audit fields, expiry, approver, denied/allowed tests. | Override flow is explicit for inspected cases. | Manual out-of-band exceptions outside the system. |
| Rule change is release-ready | Rule-to-validation map, owner approval, audit/log fields, and residual risk. | Current evidence supports release of the named rule change. | Downstream adoption where consumers were not inspected. |

## Anti-Patterns To Reject

- Treating a UI disabled state, SQL filter, fixture value, or spreadsheet copy as the rule authority without cataloging owner and enforcement.
- Closing a rule catalog from project memory, old tickets, or generated summaries without current source and validation freshness.
- Returning booleans without reason codes, evidence, or rule version for money, eligibility, audit, or compliance decisions.
- Allowing admin/support overrides without owner, allowed conditions, audit, expiry, and precedence.
- Claiming every entry point is covered when jobs, imports, retries, migrations, admin tools, or support paths were not scanned.
