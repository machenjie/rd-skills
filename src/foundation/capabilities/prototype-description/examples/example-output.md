# Example Output

```markdown
## Prototype Brief

mode_selected: async list-table

source_evidence:
- Product intent: let a finance analyst create and monitor a monthly export.
- Pattern reuse: use the existing report form and job-status table patterns.
- Freshness limit: no live render, browser, or screen-reader check was run.

surface:
- Name: Monthly export panel.
- User goal: create one export and retrieve the generated file.
- Trigger: Reports > Monthly export.

information_hierarchy:
1. Reporting period selection.
2. Eligibility summary and exclusions.
3. Submit action.
4. Job status and download action.

interaction_contract:
- Submit creates one export job and prevents duplicate submission while pending.
- Validation errors appear next to the period control and preserve input.
- Completed status exposes download.
- Failed status exposes reason and retry only when retry is safe.

states:
- Loading: skeleton summary and disabled submit.
- Empty: no prior exports, with copy explaining the first export action.
- Error: system error keeps the period input and exposes retry.
- Success: completed row exposes download and timestamp.

accessibility:
- Focus remains on the period field after validation failure.
- Job completion is announced through a status region.
- Error and success are conveyed by text plus icon, not color alone.

design_system_reuse:
- Report form: existing.
- Job status table: existing; extend only if safe retry state is not supported.

changed_prototype_to_validation_map:
- Duplicate-submit guard -> component/integration test obligation.
- Status announcement -> accessibility review or test obligation.

open_decisions:
- Final empty-state copy requires product review; non-blocking for component structure.
```
