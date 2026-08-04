# Example Output

```markdown
## Task Mode — Changed Documentation Artifact

Changed artifact: `docs/api/exports.md`

Audience and behavior mapping:
- API consumers now see that `POST /exports` returns `409` while an export is active.
- On-call operators see the `EXPORT_MAX_ROWS` default, limit, and rollback behavior.

Source grounding:
- `src/routes/exports.py` owns the active-export conflict and row-limit behavior.
- `docs/openapi.yaml` defines the public response contract.
- `tests/integration/test_exports.py` exercises the conflict response.

Changed documentation:
- Added the `409 active_export_conflict` response and example.
- Documented the `EXPORT_MAX_ROWS` default and maximum.
- Added the rollback note that queued exports keep their eligibility snapshot.

Validation result:
- Documentation examples match the current OpenAPI schema and integration fixture.

Proof limits and residual debt:
- Static comparison does not prove deployed behavior.
- The operator runbook remains unverified and is owned by the exports service team.

## Review Mode — Documentation Verdict

Verdict: `corrections_required`

Findings:
- P1: The API reference omits the source-defined `409 active_export_conflict` response.
- P2: The operator section names `EXPORT_MAX_ROWS` but not its enforced maximum.

Reviewed scope:
- `docs/api/exports.md`, `src/routes/exports.py`, `docs/openapi.yaml`, and the conflict integration fixture.

Unverified scope and proof limits:
- The deployed API and operator runbook were not inspected.
- Source and fixture agreement does not prove production behavior.

Mutation: none; review mode changed no documentation artifact.
```
