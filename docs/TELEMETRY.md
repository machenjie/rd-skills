# Telemetry, Review, and Human Promotion

ChangeForge can observe real agent execution, review it offline, and let a human
promote the findings into golden cases. This closes the loop from runtime
behavior back into the skill system **without any online self-learning**.

```text
real Codex / Claude / Copilot usage
  -> hooks / stop gate record telemetry JSONL (facts only)
  -> review-agent-telemetry.py analyzes behavior offline
  -> telemetry report + suggestions.yaml (human-review-only)
  -> a human promotes selected suggestions
  -> promote-telemetry-suggestion.py writes candidate eval/fixture files
  -> validate / eval / build verify the change
  -> next usage is more stable
```

## Telemetry Is A Fact Log, Not Auto-Learning

Telemetry records what hooks observed during a turn. It never changes skills,
routing rules, or capabilities, and nothing in this pipeline edits `SKILL.md`,
`routing-rules.yaml`, or `capabilities.yaml`. Every improvement is proposed as a
candidate and only a human decides whether to apply it.

## Where Telemetry Lives

Telemetry is operational cache, not project source and not runtime skill content:

```text
${XDG_CACHE_HOME:-~/.cache}/changeforge/telemetry/<repo_hash>/
    sessions/    # append-only JSONL fact log written by hooks
    reports/     # generated review reports
    suggestions/ # generated, human-review-only suggestions
    promoted/    # audit trail of human-approved promotions
```

`<repo_hash>` is a SHA-256 prefix of the resolved repository root, never an
absolute path. Telemetry is never written into `dist/`, never installed into a
runtime skill folder, and never treated as a personal asset corpus.

## Privacy: What Telemetry Does Not Record

Each record is a small JSON object validated by
[../src/hook-runtime/schemas/telemetry-event.v1.schema.json](../src/hook-runtime/schemas/telemetry-event.v1.schema.json).
Telemetry deliberately omits sensitive content:

- no full prompts;
- no environment variables;
- no secrets;
- no full command output (stdout);
- only the leading program name of an observed command (for example `kubectl`),
  truncated, never full arguments;
- repository and working-directory identifiers are hashed, not absolute paths;
- changed paths are recorded as relative paths and capped in number and length.

Telemetry writing always fails open: any error is logged to the hook debug log
and never interrupts the agent. Set `CHANGEFORGE_TELEMETRY=off` (or `0`, `false`,
`no`) to disable telemetry writing entirely.

## The Route Manifest

`change-forge-router` emits a machine-readable `changeforge_route` YAML block in
addition to the human-readable routing result. The manifest is what hooks,
`doctor`, telemetry review, and the eval tools read. It carries
`selected_skills`, `selected_capabilities`, `selected_domain_extensions`,
`required_references`, `required_quality_gates`, `skipped_quality_gates` (each
with a reason), `blocking_questions`, `assumptions`, and `handoff_target`.

The manifest does not replace the human-readable explanation and does not
authorize any tool to mutate skill rules. It exists so closure completeness can
be checked mechanically.

## Hooks Record, They Do Not Route

The Post-Edit Structure Gate, Risk Surface Gate, and Stop Closure Gate write
telemetry in addition to their warning-only reminders. The Stop Closure Gate
records completeness facts only: whether a `changeforge_route` manifest, changed
files, validation evidence, residual risk, and required references were present.

Hooks still cannot replace `change-forge-router`. They never call a model, never
reach the network, never modify project source, and never load every compiled
reference. See [HOOKS.md](HOOKS.md). Block mode remains reserved for the
high-confidence violations listed there (stop without validation evidence, stop
without residual risk, new common/utils/helper without reuse evidence, and
dependency file changes without dependency review).

## Step 1: Review Telemetry

`scripts/review-agent-telemetry.py` reads the JSONL fact log, groups it by
session, and writes a report plus a suggestions file. It never edits
`src/registry` or `SKILL.md`.

```bash
python3 scripts/review-agent-telemetry.py
python3 scripts/review-agent-telemetry.py --repo-hash <repo_hash> --since 2026-06-01
python3 scripts/review-agent-telemetry.py --format json --output-dir ./telemetry-out
```

Options: `--telemetry-root`, `--repo-hash`, `--since`, `--until`, `--output-dir`,
`--format markdown|json|yaml`, and the optional CI guard
`--fail-on-high-severity`. With no telemetry it prints `no samples found` and
exits 0.

It detects, among others: `missed_router`, `missed_implementation_structure`,
`missed_reuse_evidence`, `missed_language_capability`,
`missed_middleware_capability`, `missed_validation_evidence`,
`missed_residual_risk`, `possible_over_routing`,
`hook_false_positive_candidate`, and `hook_false_negative_candidate`. Every
suggestion carries `id`, `type`, `severity`, `evidence`, `affected_session`,
`suggested_action`, `promotion_target`, and `requires_human_review: true`.

## Step 2: Review Suggestions By Hand

Open `suggestions/<date>-suggestions.yaml`. Each entry is a candidate, not a
verdict. Decide which are real, which are noise, and which point at a hook false
positive or false negative. The review tool cannot and does not apply anything.

## Step 3: Promote A Suggestion Into A Candidate

`scripts/promote-telemetry-suggestion.py` turns one reviewed suggestion into a
candidate golden routing case, hook fixture, or agent-behavior sample. It is a
dry run by default and only writes with `--write`. It refuses to target skill
rule files.

```bash
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path>
python3 scripts/promote-telemetry-suggestion.py --id <suggestion-id> --suggestions <path> --write
```

Generated files carry `generated_from_telemetry: true`,
`requires_human_review: true`, and `source_suggestion_id`. They are skeletons
with TODOs. Complete them by hand, then:

1. for `evals/routing/<case>.yaml`, fill the prompt and expected route, then run
   `python3 scripts/eval-routing.py`;
2. for `evals/agent-behavior/samples/<case>.yaml`, fill the expected route and
   captured manifest, then run `python3 scripts/eval-agent-behavior.py`;
3. for `tests/fixtures/hooks/<case>.json`, wire it into a hook test and run
   `python3 -m unittest discover -s tests`.

Only commit a candidate after it is complete and the relevant validator passes.

## Step 4: Agent Behavior Eval

`scripts/eval-agent-behavior.py` scores captured, human-reviewed agent outputs
against their expected route manifest. See
[../evals/agent-behavior/README.md](../evals/agent-behavior/README.md). It never
calls a model and prints `no samples found` (exit 0) when empty.

## How This Fits The Validation Workflow

| Tool | Question it answers |
| --- | --- |
| `eval-routing.py` | Do golden routing specs (and optional captured outputs) match the rules? |
| `eval-agent-behavior.py` | Does a captured agent output satisfy its expected route manifest? |
| `review-agent-telemetry.py` | What did real agent runs miss? (advisory only) |
| `validate-hooks.py` | Are hook scripts safe, offline, and protocol-correct? |
| `validate-installation.py` | Are built `dist/` outputs and hook artifacts correct? |

`doctor` can summarize a review report with `--telemetry-report` or
`--telemetry-root`, and inspect installed project hooks with `--check-hooks`. It
never fixes telemetry and never promotes anything.

## What Stays Manual

- deciding a suggestion is real;
- completing and committing a promoted candidate;
- editing any skill rule, routing rule, or capability;
- enabling hook block mode.

Telemetry makes the loop observable. Humans keep the authority.
