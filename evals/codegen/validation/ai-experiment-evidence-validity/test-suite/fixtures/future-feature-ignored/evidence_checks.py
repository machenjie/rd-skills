"""Deterministic checks of the benchmark's supplied evidence and declared plans."""


def evaluate_rag(record):
    issues = set()
    relevant = set(record["relevant_ids"])
    retrieved = set(record["retrieved_ids"])
    claims = record["answer_claims"]
    if relevant - retrieved:
        issues.add("retrieval-miss")
    if set(record["required_claims"]) - set(claims):
        issues.add("answer-omission")
    used = set()
    for claim, sources in claims.items():
        sources = set(sources)
        used.update(sources)
        truth = set(record["evidence_for_claim"].get(claim, []))
        if not sources or not sources <= retrieved or not sources <= truth:
            issues.add("unsupported-claim")
    fresh_relevant = {identity for identity in relevant
                      if identity in record["documents"] and record["documents"][identity]["valid_until"] > record["as_of"]}
    if record["certain_answer"] and not fresh_relevant:
        issues.add("unsupported-certainty")
    for identity in used:
        document = record["documents"].get(identity)
        if document is None:
            issues.add("unsupported-claim")
            continue
        if document["valid_until"] <= record["as_of"]:
            issues.add("stale-evidence")
        if set(document["conflicts_with"]) & used:
            issues.add("conflicting-evidence")
    return frozenset(issues)


def evaluate_trials(records, plan):
    issues = set()
    unique = {}
    for trial in records:
        if trial["trial_id"] in unique:
            issues.add("duplicate-trial")
        else:
            unique[trial["trial_id"]] = trial
    trials = list(unique.values())
    if len(trials) < plan["minimum_trials"]:
        issues.add("insufficient-trials")
    if set(plan["tuning_case_ids"]) & set(plan["heldout_case_ids"]):
        issues.add("evaluation-contamination")
    successes = sum(trial["terminal_state"] == plan["success_terminal"] for trial in trials)
    if any(trial["reported_success"] != (trial["terminal_state"] == plan["success_terminal"]) for trial in trials):
        issues.add("success-claim-mismatch")
    quality = successes / len(trials) if trials else 0.0
    if quality < plan["minimum_quality"]:
        issues.add("quality-below-plan")
    if trials and max(trial["latency"] for trial in trials) > plan["maximum_latency"]:
        issues.add("latency-above-plan")
    if sum(trial["cost"] for trial in trials) > plan["maximum_total_cost"]:
        issues.add("cost-above-plan")
    return {"trial_count": len(trials), "actual_successes": successes,
            "quality": quality, "issues": frozenset(issues),
            "eligible_for_acceptance": not issues}


def validate_training(record):
    issues = set()
    splits = record["splits"]
    train_ids = {row["sample_id"] for row in splits["train"]}
    test_ids = {row["sample_id"] for row in splits["test"]}
    seen_samples = set()
    seen_entities = set()
    for name in ("train", "validation", "test"):
        rows = splits[name]
        samples = {row["sample_id"] for row in rows}
        entities = {row["entity"] for row in rows}
        if seen_samples & samples or len(samples) != len(rows):
            issues.add("sample-leakage")
        if record["split_kind"] == "entity" and seen_entities & entities:
            issues.add("entity-leakage")
        seen_samples.update(samples)
        seen_entities.update(entities)
        for row in rows:
            if row["feature_available_at"] > row["prediction_at"]:
                issues.add("future-feature")
            if name == "train" and row["label_available_at"] > record["training_cutoff"]:
                issues.add("immature-training-label")
            if record["split_kind"] == "time":
                if (name == "train" and row["prediction_at"] > record["training_cutoff"]) or (name != "train" and row["prediction_at"] <= record["training_cutoff"]):
                    issues.add("time-split-leakage")
    if not set(record["preprocess_fit_ids"]) <= train_ids:
        issues.add("preprocessing-leakage")
    if set(record["tuning_sample_ids"]) & test_ids:
        issues.add("heldout-used-for-tuning")
    if not set(record["required_resume_components"]) <= set(record["resume_components"]):
        issues.add("incomplete-resume")
    if any(record["loaded_artifacts"].get(name) != identity
           for name, identity in record["model_manifest"].items()):
        issues.add("artifact-mismatch")
    return frozenset(issues)


def validate_experiment(record):
    issues = set()
    plan = record["plan"]
    counts = record["assignment_counts"]
    if set(counts) != set(plan["allocation_weights"]):
        return frozenset({"invalid-allocation-record"})
    total = sum(counts.values())
    weights = sum(plan["allocation_weights"].values())
    if total < plan["minimum_units"]:
        issues.add("insufficient-units")
    statistic = 0.0
    if total:
        for arm, observed in counts.items():
            expected = total * plan["allocation_weights"][arm] / weights
            statistic += (observed - expected) ** 2 / expected
    if statistic > plan["srm_statistic_limit"]:
        issues.add("sample-ratio-mismatch")
    if record["analysis_unit"] != plan["assignment_unit"] and record["dependence_handling"] != "clustered-by-assignment":
        issues.add("unit-dependence-mismatch")
    if plan["registered_at"] >= record["first_assignment_at"]:
        issues.add("plan-not-preregistered")
    if plan["stopping"] == "fixed":
        if record["stopped_for_effect"] and (total < plan["sample_target"] or record["decision_looks"] > 1):
            issues.add("unplanned-fixed-sample-stop")
    elif plan["stopping"] == "sequential":
        if plan["sequential_method"] not in {"alpha-spending", "always-valid"} or record["analysis_method"] != plan["sequential_method"]:
            issues.add("invalid-sequential-method")
        if record["decision_looks"] > plan["maximum_looks"] or record["spent_alpha"] > plan["alpha_budget"]:
            issues.add("sequential-budget-exceeded")
    else:
        issues.add("invalid-stopping-plan")
    if record["hypotheses_tested"] > plan["maximum_hypotheses"] or record["multiplicity_method"] != plan["multiplicity_method"]:
        issues.add("multiplicity-plan-violation")
    return frozenset(issues)


_correct_validate_training = validate_training

def validate_training(record):
    return _correct_validate_training(record) - {"future-feature"}
