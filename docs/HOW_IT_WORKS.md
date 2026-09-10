# How it works

rd-skills chooses the professional knowledge and mechanisms needed for your
request. A normal local change can be:

```text
Task: inspect → edit → self-check → targeted validation → done
```

Analysis, multiple Tasks, and independent Review appear when they help resolve
an actual question. They are not mandatory stages around every edit.

## Professional Skill routing

You describe the outcome; the main agent selects the relevant Professional
Skill, such as backend implementation, frontend implementation, or migration
review. A Professional Skill supplies guidance about ownership, rules, failure
modes, and verification. Supporting knowledge is loaded only when the task needs
it. You do not have to learn the Skill catalog.

Routing chooses expertise. It does not decide that every task needs a planning
round or an independent reviewer. The main agent coordinates; the assigned
agents inspect source, implement, or review within their respective roles.

## Four different questions

| Mechanism | Question it answers | What it does |
| --- | --- | --- |
| Analysis | Do we know how to make the change correctly? | Resolves a specific uncertainty from current source, or answers an explicit analysis or diagnosis request. It does not edit. |
| Task | Who makes the change? | Inspects the owner, tests, and consumers, then edits within the assigned scope and checks its work. |
| Validation | Does the change pass the relevant checks? | Runs tests, builds, lint, or other appropriate observations after the final relevant edit. The Task performs this work. |
| Review | Do we need an independent second judgment? | A separate agent inspects the actual change or artifact and reports concrete defects and limits. It does not repair them. |

Validation is an activity, not a fifth agent role. A reviewer can examine tests
and their results, but independent Review does not replace validation.

## When Analysis appears

Finding a file, owner, test, or caller is ordinary Task work. A Task can inspect
and reason before editing without creating a separate Analysis assignment.

Deeper Analysis helps when inspection leaves a decision that could change the
implementation: two modules enforce conflicting rules, mixed application
versions may read a migration differently, or a retry could violate a payment
invariant. Resolve that question before the dependent edit, then continue.
An explicit request to diagnose, explain current source, or design without
editing can also be Analysis alone and end with its answer.

## How Tasks execute and split

A Task reads enough current code to choose the right owner and reuse existing
structure. It makes a bounded change, self-checks, and runs relevant validation.
For a reproducible bug, it proves the failing behavior and cause, looks for the
same pattern nearby, then verifies the repair. A later edit requires fresh
checks for the behavior it affects.

Use multiple Tasks for real dependencies, separate owners, or independently useful
work—for example, an API change and its client update with an agreed contract.
File count alone is not a reason to split. Shared-workspace writes stay serial;
parallel writes require Host-provided isolation and independent write surfaces.

## When Review helps

Use independent Review when you request it or when current evidence identifies
an important question that benefits from another judgment, especially a failure
mechanism poorly covered by local checks. For example, cross-organization invoice
access may warrant a separate examination of tenant authorization. A task ending,
a large diff, or a test passing is not by itself a reason to schedule Review.

An ordinary review defect returns to the original Task for repair and fresh
targeted validation, then the work can finish. Re-review is needed only if a
required independent judgment remains unresolved or the repair introduces a new
question requiring that judgment. A review-only request returns findings; repair
needs implementation authorization.

## Normal behavior matrix

These examples show typical choices under the stated facts, not fixed routes.
Validation below means checks of an implementation; read-only work may inspect
existing evidence and must report any missing proof.

| Request and facts | Separate Analysis | Task / edit | Validation | Independent Review |
| --- | --- | --- | --- | --- |
| Update one form's error state; owner and API behavior are clear | Usually no | Yes | Relevant component checks | Usually no |
| Fix a reproducible local null-handling bug | Usually no; Task diagnoses locally | Yes | Failing behavior before repair, regression check after | Usually no |
| Explain why a callback can create duplicates; do not edit | Yes, explicitly requested | No | No implementation to validate | Usually no |
| Share a calculation, but existing consumers disagree on rounding | If Task cannot resolve the rule conflict | After the rule is clear | Checks for affected consumers | Only for a remaining question needing independent judgment |
| Add tenant-scoped invoice access and request a security review | Only if authorization semantics remain unclear | Yes | Allowed and denied access checks | Yes, for tenant isolation |
| Review a supplied migration that removes a column immediately | Only if a specific question needs deeper investigation | No, review only | Inspect supplied compatibility evidence and state gaps | Yes, explicitly requested |
| Repair an ordinary defect found by Review within the agreed design | Usually no | Original Task repairs | Fresh targeted checks | No automatic re-review |

See the [worked examples](../examples/README.md) or their generated
[Showcase](SHOWCASE.md) for concrete requests and expected evidence.

For implementation detail, continue to [Architecture](HOOKLESS_ARCHITECTURE.md),
[Operating model](OPERATING_MODEL.md), and [Subagent model](SUBAGENT_MODEL.md).
The [documentation map](README.md) then leads to Skill authoring, validation,
and release material for maintainers.
