def media_evidence(record, policy):
    return {"failures": set(), "pts": {}, "dts": {}, "presented": []}

def simulation_evidence(record, policy):
    return {"failures": set(), "steps": [], "backlog_ms": 0, "discarded_ms": 0, "active_ms": 0, "effects": [], "score": 0, "determinism": "unproved"}

def device_evidence(record, required):
    return {"failures": set(), "epoch": record["initial_epoch"]}
