"""Deterministic accounting for recorded load, not a load generator."""


def analyse_load(planned, observations):
    counts = {name: 0 for name in ("sent", "success", "rejected", "timeout", "pending")}
    planned_latency, service_latency, queue_delay = {}, {}, {}
    seen = set()
    for row in observations:
        index = row["id"]
        if index in seen or not isinstance(index, int) or not 0 <= index < len(planned):
            raise ValueError("duplicate or unknown request")
        seen.add(index)
        start, end, outcome = row["start"], row["end"], row["outcome"]
        if start is None:
            if end is not None or outcome is not None:
                raise ValueError("unsent work has no result")
            continue
        if start < planned[index]:
            raise ValueError("start precedes planned arrival")
        counts["sent"] += 1
        queue_delay[index] = start - planned[index]
        if end is None:
            if outcome is not None:
                raise ValueError("unfinished work has no terminal result")
            counts["pending"] += 1
        else:
            if end < start or outcome not in ("success", "rejected", "timeout"):
                raise ValueError("invalid terminal outcome")
            counts[outcome] += 1
            planned_latency[index] = end - planned[index]
            service_latency[index] = end - start
    counts["intended"] = len(planned)
    counts["unsent"] = len(planned) - counts["sent"]
    return {**counts, "planned_latency": planned_latency, "service_latency": service_latency, "queue_delay": queue_delay}


def configuration_failures(measurement, policy, mode):
    failures = set()
    if measurement["quality"] < policy["min_quality"]:
        failures.add("quality")
    if measurement["p99_ms"] > policy["max_p99_ms"]:
        failures.add("tail-latency")
    if measurement["unit_cost"] > policy["max_unit_cost"]:
        failures.add("cost")
    if mode == "hosted":
        if not {"input_tokens", "output_tokens", "quota", "billed_after_cancel"} <= set(measurement.get("hosted", {})):
            failures.add("hosted-evidence")
    elif mode == "self-hosted":
        details = measurement.get("self_hosted", {})
        if not {"prefill_ms", "decode_ms", "weights_bytes", "kv_bytes", "device_bytes"} <= set(details):
            failures.add("self-hosted-evidence")
        elif details["weights_bytes"] + details["kv_bytes"] > details["device_bytes"]:
            failures.add("device-memory")
    else:
        raise ValueError("unknown deployment mode")
    return failures
