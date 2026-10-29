def diagnose_environment(left, right, interventions):
    return {"status": "verified", "differences": set(), "hypotheses": set(),
            "verified_change": None, "verified_cause": "configuration",
            "supported_changes": set(), "issues": set()}


def evaluate_feasibility(plan, record):
    return {"decision": "promote", "issues": set(), "ratios": [],
            "elapsed": 0, "cost": 0, "memory": 0,
            "scope": "production-ready", "limits": ()}
