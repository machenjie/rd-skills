# Evidence Contract

Implement pure functions in evidence_checks.py. Fixture records describe observations. They contain no expected-cause or expected-decision flags.

## Environment Comparison

diagnose_environment(left, right, interventions) compares the failing local run with the passing CI run. Both records declare code, case, input, resolved_executable, ordered path, cwd, architecture, runtime, compiler, actual dependency_graph edges, certificates, proxy, ports, permissions, services, terminal, and failure.

Resolve env_layers by env_precedence, from lowest to highest. Source names must appear exactly once in each collection. Compare effective values as env:KEY facts. Source-list order alone is immaterial. Dependency-edge, certificate, and permission ordering is immaterial. PATH ordering remains material. Missing required fields must not become optimistic defaults.

Return differences, hypotheses, supported_changes, verified_change, verified_cause, status, and issues. Classify code as application. Classify executable, architecture, runtime, compiler, and dependency graph as toolchain. Classify other environment facts as configuration. Case or input differences produce incomparable-workload.

A difference alone never verifies a cause. Each intervention supplies method, before, after, and replay records. Its before facts must match the original failure. Controlled trials keep the original workload. A minimal-reproduction may reduce case and input; these remain identical across its three records.

Admit exactly one changed fact. It must match an original difference and change to the passing run's value. The after terminal must pass. Before and replay must fail with the original failure signature and identical normalized facts. Otherwise report uncontrolled-change or unreproduced-intervention.

One supported fact verifies its category. Multiple supported facts remain inconclusive. Equal normalized facts with equal terminal outcomes are equivalent. Operation labels such as reinstall, delete-lock, and clear-cache carry no causal weight.

## Feasibility Comparison

evaluate_feasibility(plan, record) evaluates ordered baseline/candidate pairs. The plan declares a metric, maximum candidate/baseline ratio, and ratio-above-limit refutation rule. It also fixes independent_variable, baseline_value, candidate_value, fixed_factors, versions, input_ids, required_boundaries, minimum_pairs, maximum_pairs, stop_on_refutation, resource budget, and nonempty limits.

Each run declares input, factors, versions, boundary_trace, terminal, metrics, elapsed, cost, and memory. Only the independent variable may differ. Both runs must use the fixed versions and same declared input. Both traces must include every required critical boundary. A mock-wire marker does not satisfy real-wire.

Use completed runs and finite metrics. Baseline metric must be positive; candidate metric must be nonnegative. Compute the ratio. Sum elapsed and cost across all recorded runs. Memory is the maximum observed peak. Budget values are caller-supplied; equality is allowed. Negative or nonfinite resource values are invalid.

Stop after maximum_pairs, explicit refutation when enabled, exhausted time/cost, or excess memory. Later pairs produce continued-after-stop. Duplicate pair identities are invalid. Planned stopping before minimum_pairs is early-stop. A budget stop requires an exhausted budget and remains budget-exhausted. A refuted stop requires an observed refutation and the declared stop rule. Manual stopping remains early-stop.

Promote only a complete, comparable, unrefuted result within all limits. Exercise all declared inputs and minimum_pairs. One valid counterexample may discard the all-input hypothesis before the minimum under the declared refutation stop. Any evidence issue retains the prototype for further investigation.

Return decision, issues, ratios, elapsed, cost, memory, scope, and limits. Scope is always prototype-only. Promote means proceed to another bounded evaluation. It never establishes production readiness or architecture suitability.
