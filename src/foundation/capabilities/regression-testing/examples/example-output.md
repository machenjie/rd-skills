# Example Output

```markdown
## Regression Plan

Defect: Viewer could delete archived project through stale action menu.

Root cause:
- Permission check used visible menu state instead of server-side project status.

Regression test:
- Integration test sends DELETE as viewer against archived project.
- Expects 403 and no project deletion.
- Confirms audit denial event is written.

Fail-before:
- Test fails on old behavior because delete succeeds.
```
