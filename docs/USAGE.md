# Usage

rd-skills coordinates engineering work through one control prompt, four
bounded Agent Profiles, one primary Professional Skill per task, and only the
Layer 3 guidance triggered by concrete risk or technology.

Slash Skill syntax is `/skill-name`. Start with
`/engineering-control-plane`. Give observable acceptance, a bounded scope, and
a repository-native verification command when you know them. The main control
agent chooses exactly one path; task agents do not reroute themselves.

Some hosts do not provide native Slash UI or autocomplete. Put the literal
`/engineering-control-plane` in the request text in that case. It expresses
routing intent; it does not prove native Slash support.

## Copyable Direct Task Request

Use Direct Task for explicit, reversible, local work with known ownership and
verification and no material public-contract, migration, authorization,
privacy, security, financial, production, or irreversible risk.

```text
/engineering-control-plane

Goal: Add an empty-string guard to `src/example.py` without changing its public API.
Acceptance: Empty input returns the existing validation error; current valid-input behavior stays unchanged.
Allowed scope: `src/example.py` and `tests/test_example.py` only.
Verify: Run `python3 -m unittest tests.test_example`.
Stop if the owner, public contract, or verification command differs from this request.
```

Replace the paths and test command with repository facts. Expected interaction:
`main-control-agent` assigns one bounded task to `task-agent`; after the final
edit, targeted validation runs and `review-agent` reviews the actual diff and
every changed file. Ordinary findings accumulate during review and re-review
until the fixed scope and required risk dimensions are complete. Material
current-task findings from the same Review Round and Task ID return as exactly
one same-Task Repair assignment, followed by fresh validation and a covering
re-review. New material findings in that re-review use the same rule for the
next round.

## Copyable Analyzed Work Request

Use Analyzed Work when ownership, impact, or validation is unknown; multiple
modules are involved; or contract, migration, architecture, security, privacy,
financial, production, or irreversible risk may exist.

```text
/engineering-control-plane

Desired behavior: Rename the customer status field used by the API, background jobs, and analytics exports.
Known scope: The API and worker are in this repository; downstream consumers and migration order are unknown.
Acceptance: Produce a source-backed compatibility and rollout plan, identify the owning surfaces, and start only the earliest safe reversible implementation slice.
Verify: Map each acceptance item to a current test, schema check, or explicit evidence gap.
Stop for a breaking consumer decision, production data change, destructive migration, or scope outside this repository.
```

Expected interaction: `analysis-agent` reads the bounded source and returns an
Engineering Brief with ownership, invariants, consumer/failure impact,
acceptance-to-validation mapping, and the First Executable Slice. A Task DAG is
used only when real dependencies, owners, or useful parallel work exist.
The Analysis assignment and Brief have no Execution Level. The Level is computed
only after the executable slice is known, using the analysis handoff as evidence.
Implementation proceeds only within the accepted slice and receives independent
diff review.

## Copyable Review-Only Request

Use review-only when you want a non-modifying assessment of an existing
implementation diff:

```text
/engineering-control-plane

Mode: Review only. Do not edit or repair files.

Review the current implementation diff and every changed file against:
- the acceptance source at `<replace-with-real-repository-path-or-supplied-artifact>`;
- repository architecture and compatibility rules;
- validation results supplied with the diff.

Return blocking findings first with file/line evidence, then unverified scope and residual risk. If an actual diff is unavailable, report that boundary instead of inferring from a changed-file summary.
```

Before pasting, replace the acceptance-source placeholder with the real path or
supplied artifact. If no acceptance document exists, replace that bullet with
`- Acceptance: <observable criteria for this change>;` so the reviewer has an
explicit contract instead of an invented file.

Depending on normalized capability facts, `review-agent` consumes an accessible
native change reference or a supplied exact artifact. Review is blocked before
dispatch when the producer has not supplied exact evidence; only a legacy or
incomplete handoff may use one bounded pre-review recovery. The reviewer does
not repair findings or generate change artifacts.

Native change reads, evidence export, supplied delivery, and reviewer
consumption are independent capability facts. Supplied review receives actual
unified-diff content; native review receives a current reference readable by the
assigned reviewer. Static support, a digest, a path, or a command-output label
does not make Review Input Ready.

## What You Should See

For implementation work, expect these observable stages:

1. Path and Skill selection: Direct Task or Analyzed Work, one primary
   Professional Skill, and only named Layer 3 guidance.
2. A bounded task contract or Engineering Brief with scope, acceptance,
   verification, non-goals, and stop conditions.
3. A Review Input Ready implementation handoff from the latest material edit,
   including changed paths, exact change evidence, reviewer accessibility,
   fresh targeted validation, and fixed review scope.
4. Independent review of the actual latest diff and all changed files.
5. One same-Round, same-Task Repair batch for material current-task findings,
   preserving each finding's scope and proof obligations, followed by fresh
   validation and covering re-review. A later re-review finding may create the
   next same-Task batch. Scope blockers from review or re-review return to
   Analysis and adjacent findings remain record-only.
6. A visible closure handoff whose status is supported by current evidence.

After Review Input Ready dispatch, a blocked Review is valid only when required
review surface becomes unavailable, required current Evidence becomes stale,
or current Evidence invalidates protected Authority or the Engineering Brief.
It reports Reviewed Scope, Unreviewed Scope, and Proof Limit; protected
invalidation returns through Main to Delta Analysis.

No-edit validation or diff export uses before/after workspace change-set checks.
A changed or unavailable no-edit check invalidates that utility result.

## Decisions That Stay With You

rd-skills can dispatch bounded work without asking permission. It stops for a
concrete user-owned decision when work needs scope expansion, destructive or
production action, privilege elevation, data migration, replacement of
unmanaged content, or a choice not supported by evidence. It should ask one
specific question, not repeat the same preparation loop.

If a request crosses a new material risk or owner boundary, the task returns a
Scope / Risk Escalation before editing outside the accepted scope.

## Final Handoff Contents

An implementation handoff records status, task and owner, result, expected
output, changed files, exact change evidence or a reviewer-accessible native
reference, commands, validation results, last-edit/validation ordering, and the
five Review Input Ready facts. Its visible task-local
Evidence Ledger identifies current `latest-material-edit` and
`validation-passed` claims. Closure also reports independent review findings,
unverified scope, residual risk, and the next step.

Repository evidence does not prove real-host enforcement or production
correctness. Review the larger routes in the generated [Scenario
Showcase](SHOWCASE.md) and their source prompts in the [examples
index](../examples/README.md). See [AI control boundaries](AI_CONTROL_BOUNDARIES.md)
for enforcement limits and [Subagent model](SUBAGENT_MODEL.md) for detailed role
contracts.
