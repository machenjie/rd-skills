from math import isfinite


def _facts(run):
    layers = run["env_layers"]
    sources = {row["source"]: row["values"] for row in layers}
    precedence = run["env_precedence"]
    if len(sources) != len(layers) or len(set(precedence)) != len(precedence) or set(precedence) != set(sources):
        raise ValueError("environment sources need one explicit precedence position")
    environment = {}
    for source in precedence:
        environment.update(sources[source])
    facts = {key: run[key] for key in (
        "code", "case", "input", "resolved_executable", "cwd",
        "architecture", "runtime", "compiler", "proxy",
    )}
    facts["path"] = tuple(run["path"])
    facts["dependency_graph"] = tuple(sorted(tuple(edge) for edge in run["dependency_graph"]))
    for key in ("certificates", "permissions"):
        facts[key] = tuple(sorted(set(run[key])))
    for key in ("ports", "services"):
        facts[key] = tuple(sorted(run[key].items()))
    facts.update({f"env:{key}": value for key, value in environment.items()})
    return facts


def _differences(left, right):
    return {key for key in left.keys() | right.keys() if left.get(key) != right.get(key)}


def _category(key):
    if key == "code":
        return "application"
    if key in {"resolved_executable", "architecture", "runtime", "compiler", "dependency_graph"}:
        return "toolchain"
    return "configuration"


def diagnose_environment(left, right, interventions):
    before, after = _facts(left), _facts(right)
    differences = _differences(before, after)
    hypotheses = {_category(key) for key in differences - {"case", "input"}}
    issues, supported = set(), set()
    comparable = not differences.intersection({"case", "input"})
    reproduced = left["terminal"] == "fail" and right["terminal"] == "pass"
    if not comparable:
        issues.add("incomparable-workload")
    if not reproduced and (differences or left["terminal"] != right["terminal"]):
        issues.add("no-failing-passing-comparison")
    for trial in interventions:
        first, changed, replay = (trial[key] for key in ("before", "after", "replay"))
        a, b, c = (_facts(item) for item in (first, changed, replay))
        delta = _differences(a, b)
        method = trial["method"]
        # A minimal reproduction may reduce only the workload, not environment facts.
        ignored = {"case", "input"} if method == "minimal-reproduction" else set()
        linked = method in {"controlled", "minimal-reproduction"} and all(
            a.get(key) == before.get(key) for key in a.keys() | before.keys() if key not in ignored
        )
        isolated = len(delta) == 1 and delta <= differences - {"case", "input"}
        if not comparable or not linked or not isolated or any(b.get(key) != after.get(key) for key in delta):
            issues.add("uncontrolled-change")
            continue
        same_failure = (
            reproduced and first["terminal"] == replay["terminal"] == "fail"
            and first["failure"] == replay["failure"] == left["failure"]
            and changed["terminal"] == "pass" and a == c
        )
        if not same_failure:
            issues.add("unreproduced-intervention")
            continue
        supported.update(delta)
    verified_change = next(iter(supported)) if len(supported) == 1 else None
    if len(supported) > 1:
        issues.add("multiple-supported-changes")
    status = "verified" if verified_change else "inconclusive"
    if not differences and left["terminal"] == right["terminal"]:
        status = "equivalent"
    return {
        "status": status, "differences": differences, "hypotheses": hypotheses,
        "verified_change": verified_change,
        "verified_cause": _category(verified_change) if verified_change else None,
        "supported_changes": supported, "issues": issues,
    }


def evaluate_feasibility(plan, record):
    hypothesis = plan["hypothesis"]
    budget = plan["budget"]
    if (
        not hypothesis.get("metric") or hypothesis.get("refutation") != "ratio-above-limit"
        or not isinstance(hypothesis.get("maximum_ratio"), (int, float))
        or not isfinite(hypothesis["maximum_ratio"]) or hypothesis["maximum_ratio"] <= 0
        or not plan["required_boundaries"] or not plan["input_ids"] or not plan["versions"]
        or not plan["limits"] or not 1 <= plan["minimum_pairs"] <= plan["maximum_pairs"]
        or any(not isfinite(value) or value <= 0 for value in budget.values())
        or set(budget) != {"elapsed", "cost", "memory"}
    ):
        raise ValueError("a falsifiable bounded plan is required")
    issues, seen, covered_inputs = set(), set(), set()
    ratios, elapsed, cost, memory = [], 0, 0, 0
    stopped, refuted, exhausted = False, False, False
    required = set(plan["required_boundaries"])
    variable = plan["independent_variable"]
    for index, pair in enumerate(record["pairs"], start=1):
        if stopped:
            issues.add("continued-after-stop")
        if pair["id"] in seen:
            issues.add("duplicate-pair")
        seen.add(pair["id"])
        base, candidate = pair["baseline"], pair["candidate"]
        pair_issues = set()
        expected_base = dict(plan["fixed_factors"], **{variable: plan["baseline_value"]})
        expected_candidate = dict(plan["fixed_factors"], **{variable: plan["candidate_value"]})
        if base["factors"] != expected_base or candidate["factors"] != expected_candidate:
            pair_issues.add("incomparable-baseline")
        if base["input"] != candidate["input"] or base["input"] not in plan["input_ids"]:
            pair_issues.add("incomparable-input")
        if base["versions"] != plan["versions"] or candidate["versions"] != plan["versions"]:
            pair_issues.add("version-drift")
        for run in (base, candidate):
            if not required <= set(run["boundary_trace"]):
                pair_issues.add("missing-boundary")
            if run["terminal"] != "completed":
                pair_issues.add("incomplete-trial")
            if any(not isfinite(run[key]) or run[key] < 0 for key in ("elapsed", "cost", "memory")):
                raise ValueError("resource measurements must be finite and nonnegative")
            elapsed += run["elapsed"]
            cost += run["cost"]
            memory = max(memory, run["memory"])
        metric = hypothesis["metric"]
        numerator, denominator = candidate["metrics"].get(metric), base["metrics"].get(metric)
        if any(not isinstance(value, (int, float)) or not isfinite(value) for value in (numerator, denominator)):
            pair_issues.add("invalid-measurement")
        elif numerator < 0 or denominator <= 0:
            pair_issues.add("invalid-measurement")
        if not pair_issues:
            ratio = numerator / denominator
            ratios.append(ratio)
            covered_inputs.add(base["input"])
            refuted |= ratio > hypothesis["maximum_ratio"]
        issues.update(pair_issues)
        if elapsed > budget["elapsed"] or cost > budget["cost"] or memory > budget["memory"]:
            issues.add("over-budget")
        exhausted = elapsed >= budget["elapsed"] or cost >= budget["cost"] or memory > budget["memory"]
        stopped = exhausted or index >= plan["maximum_pairs"] or (refuted and plan["stop_on_refutation"])
    reason = record["stop_reason"]
    if reason == "budget":
        issues.add("budget-exhausted" if exhausted else "invalid-stop")
    elif reason == "refuted":
        if not refuted or not plan["stop_on_refutation"]:
            issues.add("invalid-stop")
    elif reason == "planned":
        if len(record["pairs"]) < plan["minimum_pairs"]:
            issues.add("early-stop")
    elif reason == "manual":
        issues.add("early-stop")
    else:
        issues.add("invalid-stop")
    # One valid counterexample can refute the all-input hypothesis under its declared stop rule.
    if not refuted:
        if len(ratios) < plan["minimum_pairs"]:
            issues.add("insufficient-pairs")
        if covered_inputs != set(plan["input_ids"]):
            issues.add("missing-input")
    decision = "retain" if issues else ("discard" if refuted else "promote")
    return {
        "decision": decision, "issues": issues, "ratios": ratios,
        "elapsed": elapsed, "cost": cost, "memory": memory,
        "scope": "prototype-only", "limits": tuple(plan["limits"]),
    }


_diagnose_with_evidence = diagnose_environment


def diagnose_environment(left, right, interventions):
    result = _diagnose_with_evidence(left, right, interventions)
    # Single fault: promote a one-field observed delta without intervention evidence.
    if not interventions and len(result["differences"]) == 1:
        key = next(iter(result["differences"]))
        if key not in {"case", "input"}:
            result.update(status="verified", verified_change=key, verified_cause=_category(key))
    return result
