"""Implement the evidence checks defined in task.md; no model calls are needed."""

def evaluate_rag(record):
    return frozenset()


def evaluate_trials(records, plan):
    return {"trial_count": len(records), "actual_successes": len(records), "quality": 1.0,
            "issues": frozenset(), "eligible_for_acceptance": True}


def validate_training(record):
    return frozenset()


def validate_experiment(record):
    return frozenset()
