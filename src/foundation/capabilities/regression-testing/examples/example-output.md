# Example Output

```markdown
## Regression Recurrence Decision

Defect: a viewer could delete an archived project through a stale action menu.
Failure mechanism: the delete command authorized from menu visibility and omitted the authoritative project-state and role check.

Guard boundary:
- Integration guard sends the delete command as a viewer against an archived project.
- It asserts denial, no project deletion, no downstream delete event, and a bounded audit-denial record.
- A unit-only guard was rejected because command authorization and persistence state are causal.

Counterfactual:
- The guard fails on the protected unfixed revision because deletion succeeds, then passes after the final fix.

Same-pattern scan:
- Active and archived project entry points, bulk delete, and API callers were inspected.
- Bulk delete had the same missing check and now shares the guard; no other reachable match was found.

Proof limit:
- The guard does not establish browser menu freshness or every tenant/object authorization path; those remain with frontend and security proof.
```
