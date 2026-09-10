# Examples

These scenarios show how rd-skills selects mechanisms for the facts in a request.
They are illustrative expectations, not executable demo repositories or evidence
that a live host performed the work.

Start with [the local form change](02-frontend-form-state-change/prompt.md): one
Task inspects, edits, self-checks, and validates, without separate Analysis or
independent Review. Then compare the other cases:

| Example | Why the mechanisms differ |
| --- | --- |
| [Local form change](02-frontend-form-state-change/expected-route.md) | The existing owner and behavior are clear; targeted validation is sufficient. |
| [Invoice permissions](01-backend-permission-change/expected-route.md) | Implementation plus an explicitly requested security Review of cross-organization access. An ordinary defect returns to the original Task for repair and validation. |
| [Migration review](03-data-migration-review/expected-route.md) | Review only, with findings about compatibility and rollback; no repair is authorized. |
| [Calculation refactor](04-structure-refactor-placement/expected-route.md) | The user explicitly asks to resolve conflicting calculation rules before editing. Analysis answers that question; implementation follows only when the rule is clear. |

Each example includes:

- `prompt.md`: the user request and scenario facts.
- `expected-route.md`: selected expertise, role assignments, and why they are needed.
- `expected-evidence.md`: source to inspect, relevant validation, any selected independent Review, and result limits.

The [Scenario Showcase](../docs/SHOWCASE.md) is generated from these files. Change
the example source, then run
`python3 scripts/generate-examples-showcase.py --out docs/SHOWCASE.md`.
For the shared mental model, read [How it works](../docs/HOW_IT_WORKS.md).
