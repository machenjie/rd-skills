# Benchmarks

rd-skills uses bounded, reproducible repository evaluations. Benchmarking is
limited to deterministic routing, lightweight trajectories, captured behavior
and pressure fixtures, professional-quality checks, and code-generation
definition and harness checks.

## Suites

| Suite | Purpose | Command |
| --- | --- | --- |
| Routing | Verify one primary Professional Skill, triggered Layer 3 guidance, and one Review Skill. | `python3 scripts/eval-routing.py` |
| Lightweight | Verify bounded control-plane trajectories and preparation-loop behavior. | `python3 scripts/eval-agent-lightweight.py` |
| Rendered context | Count exact deterministic instruction tokens across built host/profile artifacts and fixture dispatches. | `python3 scripts/eval-rendered-context-budget.py` |
| Behavior | Check human-reviewed handoffs against observable route and evidence contracts. | `python3 scripts/eval-agent-behavior.py` |
| Pressure | Check captured responses for boundary preservation under pressure. | `python3 scripts/eval-pressure-behavior.py` |
| Professional | Check Skill structure, decision quality, coverage, and promoted samples. | See commands below. |
| Code generation | Validate case definitions, checked-in harnesses, and starter negative controls. | `python3 scripts/validate-codegen-benchmarks.py` and `python3 scripts/run-codegen-benchmarks.py --limit 3` |

## Scenario Coverage

The deterministic corpus covers:

- single-file bug fix;
- single-module feature;
- multi-module feature;
- diagnosis;
- review-only work;
- repair and re-review;
- public API change;
- data migration;
- security work;
- concurrency and consistency;
- release and rollback.
- paired positive and neighboring negative routes for all 13 Domain Skills;
- capability-driven Utility no-edit with exact pre-observation, operation, and
  identical post-observation sequencing, including changed and unavailable
  workspace-state failures;
- adapter-owned native diff safeguards: the Codex projection statically requires
  `--no-pager`, `--no-ext-diff`, and `--no-textconv`, while adapters without a
  native diff mode declare no native command safeguards;
- anchored progress for three-dispatch, complex/high-risk, and long work;
- current shared-workspace serial writes; and
- a conditional isolated-write parallel contract, not a current Host capability.

These checks validate deterministic fixtures and static adapter configuration.
They do not prove that a running host enforced its declared native controls.

## Professional Coverage Evidence

`professional-coverage-matrix` schema version 3 keeps static authoring quality
separate from deterministic coverage. Each row has `authoring_status`, six
explicit `coverage_states`, evidence case IDs and counts, and a policy-derived
`coverage_gate_status`. A registered Skill with no route or behavior fixture is
`not-required` unless the checked-in release policy requires coverage; it is
never reported as a generic coverage pass.

Every registered Domain Skill requires positive routing, neighboring negative
routing, and captured behavior evidence. Each Domain has two major routing
families. Every family has canonical and paraphrased positive fixtures. Each
Domain also has one transition-positive fixture. It has one unchanged-paraphrase
negative control. A positive route requires a domain signal and a boundary
signal. Explicit migration to that boundary wins over legacy context. Explicit
absence, unchanged behavior, or documentation-only copy keeps adjacent work out.

Positive and negative routing coverage comes from fresh `eval-routing.py`
actual results. Expected routes never count as coverage evidence. A negative
fixture uses `excluded_skills`. It passes only when the actual route omits every
excluded Primary, Review, and Layer 3 Skill.

Registry trigger and boundary signals are atomic. The routing validator compares
each atom with its oracle family and Router row. Whole-string copying is not
evidence.

`scripts/deterministic_route_oracle.py` is the shared fixture oracle. It is
test-only, lives outside `src/`, and is not installed. It does not dispatch
runtime work or add a second routing control plane.

Behavior coverage requires a passing positive captured benchmark with no
forbidden-behavior hit. Expected-fail fixtures are adversarial negative controls
and do not count as behavior coverage. Pressure coverage counts a fixture's
executed Primary and selected Layer 3 Skills; a merely declared Review Skill is
not execution evidence.

Release-critical captured benchmarks additionally require every declared hidden
risk, evidence obligation, and output obligation, no forbidden behavior in the
with-Skill capture, a positive obligation delta, and at least one forbidden
behavior in the Baseline capture. Every fixture declares its expected stage,
and normalized obligations must be unique within and across the decision groups
that contribute to the score. These contracts prove deterministic fixture
quality only, not fresh model behavior.

## Local Commands

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/eval-routing.py
python3 scripts/eval-agent-lightweight.py
python3 scripts/eval-rendered-context-budget.py
python3 scripts/eval-context-control-plane.py
python3 scripts/eval-agent-behavior.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/eval-pressure-behavior.py
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
```

Without `--candidate-dir` or `--candidate-root`, the code-generation runner
does not generate or evaluate an implementation. It validates the checked-in
harness and confirms executable assertions reject the incomplete starter. A
candidate outcome may be claimed only from an explicitly supplied candidate;
the default command does not write a tracked outcome report.

## Evidence Limits

Reports must label static checks, deterministic fixture results, and captured
fixtures precisely. Code-generation command output must distinguish definition
and harness/negative-control checks from explicit candidate evaluation. A
structural step proxy is neither wall-clock evidence nor production proof. A
scenario pass proves only its fixture contract; it does not prove real-host
Profile startup, host performance, provider behavior, production accuracy, or
installed user experience.

The rendered-context suite requires fresh builds of all three delivery
profiles. It excludes host system prompts, tool schemas, conversation history,
repository reads, diffs, and command output, and therefore must not be reported
as observed total model context. Dispatch Capsule text is rendered only from a
versioned structured evaluation fixture and checked against its canonical hash;
typed semantic checks separately reject placeholder, repeated-token, and
low-diversity fixture fields after field-specific path, command, input, and
Utility-schema validation. The renderer is not shipped. Exact duplicate-rule
accounting counts every extra normalized non-overlapping block occurrence,
including repeats within a single loaded component. Calibration reports the
otherwise-valid nearest-rank P50/P90/P95/P99/max distribution without applying
budget to selection or exit. Conformance records Core-derived soft/hard limits,
observed maxima, both margins, growth advisories, and hard failures. Temporal
growth distribution is explicit as unavailable until a comparable prior valid
population exists.

## Rendered Context Budget Contract

<!-- BEGIN CHANGEFORGE CONTEXT BUDGET PROJECTION: benchmarks-rendered-context-budget -->
Source: `src/control-model/core-contracts.json#/context_budget_contract`.

Budget taxonomy and all Runtime/Rendered limits are owned only by Core. Budget is a cost guardrail and never changes routing, required context, or correctness obligations.

Authoring Budget classes: Main Prompt, Control Skill, Professional Skill, Foundation, Domain.
Resident Runtime Budget classes: Main always-loaded.
Dispatch Composition Budget classes: Direct Task, Analyzed Task, Analysis, Review, Utility.
Runtime Dynamic Context classes: Repository Reads, Diff, Command Output, Tool System Prompt, Conversation History; observation-only, with host conversation compaction out of scope.

| Category | Context | Soft target | Hard ceiling | Calibration status |
| --- | --- | ---: | ---: | --- |
| Resident Runtime Budget | Main always-loaded | 2305 | 2650 | provisional-migration-value |
| Dispatch Composition Budget | Direct Task dispatch | 3000 | 3200 | provisional-migration-value |
| Dispatch Composition Budget | Analyzed Task dispatch | 6000 | 6500 | provisional-migration-value |
| Dispatch Composition Budget | Analysis dispatch | 4500 | 5000 | provisional-migration-value |
| Dispatch Composition Budget | Review dispatch | 3700 | 4000 | provisional-migration-value |
| Dispatch Composition Budget | Utility dispatch | 2000 | 2500 | provisional-migration-value |

Soft-target overage is a growth advisory; hard-ceiling overage fails Conformance. Calibration does not apply either limit to candidate selection or exit.
Required routing, Professional, Domain, Layer 3, Reference, Review, and Evidence context is never truncated to satisfy a budget.

Tokenizer: `o200k_base`. Exact duplicate-rule ratio gate: `0.03`.
<!-- END CHANGEFORGE CONTEXT BUDGET PROJECTION: benchmarks-rendered-context-budget -->
