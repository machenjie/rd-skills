# Reports

This directory contains generated or captured evidence for the Hookless
ChangeForge authoring system. Reports are snapshots; rerun their owning command
against the current tree before using them for a release decision.

Core reproducible reports:

- `routing-eval.*`: deterministic route-once fixtures.
- `hookless-control-plane-eval.*`, `rendered-context-budget.*`, and
  `context-control-plane-eval.*`: observable structural trajectories plus exact
  deterministic rendered-instruction token budgets. These are not host-observed
  total context or wall-clock evidence. Parallel-write reduction is a conditional
  isolated-workspace contract; current supported-host writes remain serial.
  Fixture Capsule text comes from an evaluator-only versioned structured
  contract and canonical hash, not hand-written dispatch text. Hashes detect
  drift; typed semantic checks independently reject placeholder or
  low-diversity prose and malformed path, command, input, or Utility state.
- `skill-professionalism-eval.*`, `professional-coverage-matrix.*`,
  `professional-benchmarks-*`, and `professionalism-regression-*`: static and
  captured professional quality evidence.
- `installation-validation.*`: standard Skill/Profile installation evidence.

The local Full Regression regenerates the principal reports once through Core:

```bash
python3 scripts/eval-core-principles.py --gate authoring
```

The individual owners below are diagnostics for a verified Core failure, not a
second regression path:

```bash
python3 scripts/build.py --profile recommended
python3 scripts/build.py --profile full
python3 scripts/build.py --profile dev
python3 scripts/eval-routing.py
python3 scripts/eval-agent-lightweight.py
python3 scripts/eval-rendered-context-budget.py
python3 scripts/eval-context-control-plane.py
python3 scripts/eval-skill-professionalism.py
python3 scripts/eval-professional-benchmarks.py
python3 scripts/validate-professional-routing-coverage.py
python3 scripts/eval-professional-agent-samples.py --promoted-only --strict
python3 scripts/validate-professionalism-regression.py --strict
python3 scripts/validate-installation.py
```

The complete Formal Release entrypoint is
`python3 scripts/eval-core-principles.py --gate formal-release`; Core runs each
declared producer once in dependency order, routing every intermediate report
write and read through the ignored head-scoped `producer-reports/` staging
directory rather than this tracked directory. The sole machine-readable
professionalism readiness authority is
`professionalism-regression-report.json`. Formal Release additionally emits
`professionalism-regression-report.md` as a human presentation projection;
the final head-scoped `reports/` scene contains exactly the Core and
professionalism JSON/Markdown pair. Markdown is not a second authority and Core
authoring does not refresh it.
`validate-productization-assets.py` validates the saved JSON's closed semantics
without rerunning the professionalism producer.

Code-generation definitions and their checked-in harness/negative controls are
validated separately:

```bash
python3 scripts/validate-codegen-benchmarks.py
python3 scripts/run-codegen-benchmarks.py --limit 3
```

Those default commands do not evaluate a generated candidate or write a
tracked code-generation outcome report. Static trajectories, captured
fixtures, harness checks, and simulated installation do not prove real-host
Profile startup, wall-clock performance, production accuracy, or installed
user experience.

Do not commit raw prompts, secrets, environment variables, private paths, full
command output, personal archives, or user-specific content in reports.
